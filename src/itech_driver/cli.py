"""Command-line interface for the power supply driver."""

import argparse
import sys
from typing import Optional
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
    discover_parser.add_argument('--baudrate', type=int, default=9600)

    # Control command
    control_parser = subparsers.add_parser('control', help='Control instrument')
    control_parser.add_argument('--resource', required=True, help='VISA resource string')
    control_parser.add_argument('--model', help='Instrument model')
    control_parser.add_argument('--voltage', type=float, help='Set voltage')
    control_parser.add_argument('--current', type=float, help='Set current')
    control_parser.add_argument('--output', choices=['on', 'off'], help='Output state')

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
                      probe_vcp=args.vcp, baudrate=args.baudrate)
    for device in report.devices:
        print(device.identity.raw)
        for endpoint in device.endpoints:
            print(f"  {endpoint.interface}: {endpoint.address}")
    for diagnostic in report.diagnostics:
        print(diagnostic, file=sys.stderr)


def control_instrument(args) -> None:
    """Control an instrument."""
    try:
        if args.model:
            instr = create_instrument(args.model, args.resource)
        else:
            instr = auto_detect_instrument(args.resource)

        with instr:
            print(f"Connected to: {instr.identify()}")

            if args.voltage is not None or args.current is not None or args.output is not None:
                from .instruments import ITM3900D
                if not isinstance(instr, ITM3900D):
                    raise ValueError("setting changes require an identified IT-M3900D")
                from .identity import is_itm3900d
                from scpi_driver_core.scpi.parsers import parse_identity
                if not is_itm3900d(parse_identity(instr.identify())):
                    raise ValueError("instrument identity does not match IT-M3900D")
                with instr.remote_mode():
                    if args.voltage is not None:
                        instr.source.voltage_set(args.voltage)
                        print(f"Set voltage to {args.voltage}V")

                    if args.current is not None:
                        instr.source.current_set(args.current)
                        print(f"Set current to {args.current}A")

                    if args.output == 'on':
                        instr.output.state_set(True)
                        print("Output enabled")
                    elif args.output == 'off':
                        instr.output.state_set(False)
                        print("Output disabled")

            # Read back values
            voltage = instr.source.voltage_query()
            current = instr.source.current_query()
            print(f"Setpoints: {voltage:.4f}V, {current:.4f}A")



    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def control_main() -> None:
    main(['control', *sys.argv[1:]])


if __name__ == '__main__':
    main()
