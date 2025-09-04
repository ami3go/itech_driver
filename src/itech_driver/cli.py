"""Command-line interface for the power supply driver."""

import argparse
import sys
from typing import Optional
from .instruments import create_instrument, auto_detect_instrument


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="ITECH Power Supply Control")

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Discover instruments')

    # Control command
    control_parser = subparsers.add_parser('control', help='Control instrument')
    control_parser.add_argument('--resource', help='VISA resource string')
    control_parser.add_argument('--model', help='Instrument model')
    control_parser.add_argument('--voltage', type=float, help='Set voltage')
    control_parser.add_argument('--current', type=float, help='Set current')
    control_parser.add_argument('--output', choices=['on', 'off'], help='Output state')

    args = parser.parse_args()

    if args.command == 'discover':
        discover_instruments()
    elif args.command == 'control':
        control_instrument(args)
    else:
        parser.print_help()


def discover_instruments() -> None:
    """Discover and list available instruments."""
    import pyvisa
    rm = pyvisa.ResourceManager()
    resources = rm.list_resources()

    print("Available instruments:")
    for resource in resources:
        print(f"  {resource}")
        try:
            instr = auto_detect_instrument(resource, timeout=1000)
            idn = instr.identify()
            print(f"    IDN: {idn}")
            instr.close()
        except Exception as e:
            print(f"    Error: {e}")


def control_instrument(args) -> None:
    """Control an instrument."""
    try:
        if args.model:
            instr = create_instrument(args.model, args.resource)
        else:
            instr = auto_detect_instrument(args.resource)

        print(f"Connected to: {instr.identify()}")

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
        print(f"Measured: {voltage:.4f}V, {current:.4f}A")

        instr.close()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()