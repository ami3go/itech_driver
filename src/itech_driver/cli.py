"""Command-line interface for the power supply driver."""

import argparse
import sys
import math
import time
from scpi_driver_core import ConfigurationError, SafetyGuardError
from .capabilities import ApplicationLimits, Range
from .output_lifecycle import request_output_on, request_output_off
from .instruments import create_instrument, auto_detect_instrument


def main(argv=None) -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="ITECH Power Supply Control")

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Discover instruments')
    discover_parser.add_argument('--subnet')
    discover_parser.add_argument('--port', type=int, default=30000)
    discover_parser.add_argument('--timeout', type=int, default=1000)
    discover_parser.add_argument('--vcp', action='store_true')
    discover_parser.add_argument('--no-visa', action='store_true', help='Skip VISA enumeration')
    discover_parser.add_argument('--no-mdns', action='store_true', help='Skip mDNS enumeration')
    discover_parser.add_argument('--baudrate', type=int, default=9600)

    # Control command
    control_parser = subparsers.add_parser('control', help='Control instrument')
    control_parser.add_argument('--resource', required=True, help='VISA resource string')
    control_parser.add_argument('--model', help='Instrument model')
    control_parser.add_argument('--voltage', type=float, help='Set voltage')
    control_parser.add_argument('--current', type=float, help='Set current')
    control_parser.add_argument('--output', choices=['on', 'off'], help='Output state')

    control_parser.add_argument('--max-voltage', type=float, help='Application voltage ceiling (V)')
    control_parser.add_argument('--max-current', type=float, help='Application current ceiling (A)')
    control_parser.add_argument('--max-power', type=float, help='Application power ceiling (W)')
    control_parser.add_argument('--authorize-output', action='store_true', help='Explicitly authorize one supervised ON request')
    control_parser.add_argument('--hold-seconds', type=float, help='Explicit finite supervised ON duration; then request OFF')
    control_parser.add_argument('--max-residual-voltage', type=float, help='OFF verification residual voltage (V)')
    control_parser.add_argument('--max-residual-current', type=float, help='OFF verification residual current (A)')

    args = parser.parse_args(argv)

    if args.command == 'discover':
        discover_instruments(args)
    elif args.command == 'control':
        control_instrument(args)
    else:
        parser.print_help()


def discover_instruments(args=None) -> None:
    """CLI entry point; enumerate and query identities only."""
    from .discovery import discover_instruments as discover
    if args is None:
        main(["discover", *sys.argv[1:]])
        return
    report = discover(subnet=args.subnet, port=args.port, timeout=args.timeout,
                      probe_vcp=args.vcp, baudrate=args.baudrate,
                      use_visa=not args.no_visa, use_mdns=not args.no_mdns)
    for device in report.devices:
        print(device.identity.raw)
        for endpoint in device.endpoints:
            print(f"  {endpoint.interface}: {endpoint.address}")
    for diagnostic in report.diagnostics:
        print(diagnostic, file=sys.stderr)


def _valid_number(value, *, positive=False):
    return (type(value) in (int, float) and math.isfinite(value)
            and (value > 0 if positive else value >= 0))


def _control_policy(args):
    """Validate the complete request before opening any transport."""
    settings = args.voltage is not None or args.current is not None
    enabling = args.output == "on"
    disabling = args.output == "off"
    for value in (args.voltage, args.current):
        if value is not None and not _valid_number(value):
            raise ConfigurationError("setpoints must be finite and nonnegative")
    if disabling and settings:
        raise ConfigurationError("OFF and setting changes must be separate requests")
    if enabling and not args.authorize_output:
        raise SafetyGuardError("ON requires --authorize-output")
    if enabling and not _valid_number(args.hold_seconds):
        raise ConfigurationError("ON requires finite nonnegative --hold-seconds")
    if not enabling and (args.authorize_output or args.hold_seconds is not None):
        raise ConfigurationError("activation options require --output on")
    if enabling or disabling:
        if not all(_valid_number(x) for x in
                   (args.max_residual_voltage, args.max_residual_current)):
            raise ConfigurationError("output control requires explicit finite residual voltage/current limits")
    if settings or enabling:
        ceilings = (args.max_voltage, args.max_current, args.max_power)
        if not all(_valid_number(x, positive=True) for x in ceilings):
            raise ConfigurationError("setting changes and ON require positive finite --max-voltage/current/power")
        app = ApplicationLimits(*(Range(0, x) for x in ceilings))
        for value, bound in ((args.voltage, app.voltage), (args.current, app.current)):
            if value is not None:
                bound.validate(value)
        return app
    return None


def _verified_off(instr, args):
    result = request_output_off(instr, max_residual_v=args.max_residual_voltage,
                                 max_residual_a=args.max_residual_current)
    if result.outcome != "instrument_below_limits":
        raise SafetyGuardError(f"OFF outcome {result.outcome}; physical state not confirmed")
    print("Instrument reports OFF and residuals within caller limits; physical isolation not established.")


def _run_supervised_on(instr, args, caps):
    generation = instr.session.generation
    attempted = False

    def cleanup():
        if instr.session.is_connected and instr.session.generation == generation:
            _verified_off(instr, args)
        else:
            raise SafetyGuardError("No automatic reconnect or OFF replay. Output state UNKNOWN; use independent bench safety procedure.")

    try:
        try:
            result = request_output_on(instr, authorized=True,
                max_voltage_v=caps.voltage.maximum,
                max_current_a=caps.current.maximum,
                max_power_w=caps.power_limit.maximum)
        except KeyboardInterrupt:
            # Interrupt may have arrived after transmission, so conservatively
            # attempt one same-session OFF, even if preflight was interrupted.
            attempted = True
            raise
        # Helper raises on rejected preflight before ON; return means an ON attempt.
        attempted = True
        if result.outcome != "observed" or result.programmed is not True:
            raise SafetyGuardError("ON outcome unknown; physical output state unconfirmed")
        print("Instrument reports output ON; supervised interval started.")
        time.sleep(args.hold_seconds)
    except BaseException as primary:
        if attempted:
            try:
                cleanup()
            except BaseException as error:
                # Preserve the primary failure, but explicitly report cleanup failure.
                print(f"Cleanup failed: {error}; physical output state UNKNOWN.", file=sys.stderr)
                if hasattr(primary, "add_note"):
                    primary.add_note(f"OFF cleanup failed: {error!r}")
        raise
    else:
        cleanup()


def control_instrument(args) -> None:
    """Read-only by default; setting and output operations are explicit."""
    try:
        app = _control_policy(args)
        settings = args.voltage is not None or args.current is not None
        mutating = settings or args.output is not None
        kwargs = {"require_remote": True, "application_limits": app} if mutating else {}
        if args.model:
            instr = create_instrument(args.model, args.resource, **kwargs)
        else:
            instr = auto_detect_instrument(args.resource, **kwargs)
        with instr:
            from .instruments import ITM3900D
            identity = instr.identity_snapshot()
            print(f"Connected to: {identity.raw}")
            if not mutating:
                if isinstance(instr, ITM3900D) and instr.model_descriptor(refresh=False) is not None:
                    print(f"Setpoints: {instr.source.voltage_query():.4f}V, {instr.source.current_query():.4f}A")
                return
            if not isinstance(instr, ITM3900D) or instr.model_descriptor(refresh=False) is None:
                raise SafetyGuardError("setting changes require a recognized rated IT-M3900D")
            caps = None
            if settings or args.output == "on":
                # Validate the entire request and current output state before
                # remote mode or any setting write.
                caps = instr.discover_capabilities()
                for value, bound in ((args.voltage, caps.voltage), (args.current, caps.current)):
                    if value is not None:
                        bound.validate(value)
                if instr.output.state_query() is not False:
                    raise SafetyGuardError("setting changes or ON require output initially OFF")
            with instr.remote_mode():
                for quantity in ("voltage", "current"):
                    value = getattr(args, quantity)
                    if value is not None:
                        getattr(instr.source, quantity + "_set")(value)
                        actual = getattr(instr.source, quantity + "_query")()
                        if actual != value:
                            raise SafetyGuardError(f"{quantity} readback mismatch: requested {value}, received {actual}")
                        print(f"Verified {quantity} setpoint: {actual}")
                if args.output == "on":
                    _run_supervised_on(instr, args, caps)
                elif args.output == "off":
                    _verified_off(instr, args)
    except (Exception, KeyboardInterrupt) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def control_main() -> None:
    main(['control', *sys.argv[1:]])


if __name__ == '__main__':
    main()
