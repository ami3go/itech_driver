#!/usr/bin/env python3
"""
ITECH IT-M3900D Example with Local Module Import
This script demonstrates how to use the local module without installing it.
"""

import sys
import os
import time

# Add the local module to Python path
# Adjust the path based on your directory structure
current_dir = os.path.dirname(os.path.abspath(__file__))
module_path = os.path.abspath(os.path.join(current_dir, '..', 'src'))
if module_path not in sys.path:
    sys.path.insert(0, module_path)
    print(f"Added to path: {module_path}")

try:
    from itech_driver import create_instrument

    print("Successfully imported local module!")
except ImportError as e:
    print(f"Failed to import module: {e}")
    print("Please check the path configuration.")
    sys.exit(1)


def main():
    """Main example function."""
    # Replace with your instrument's VISA address
    resource_string = 'TCPIP0::192.168.1.100::inst0::INSTR'

    print("IT-M3900D Local Module Example")
    print("=" * 50)

    try:
        # Try auto-detection first
        print("Attempting to auto-detect instrument...")
        psu = auto_detect_instrument(resource_string, timeout=3000)

        # Identify the instrument
        idn = psu.identify()
        print(f"Connected to: {idn}")

        # Basic operations
        print("\nPerforming basic operations...")
        psu.source.voltage_set(5.0)
        psu.source.current_set(0.1)

        print("Enabling output for 3 seconds...")
        psu.output.state_set(True)
        time.sleep(3)

        # Take measurements
        voltage = psu.measurement.voltage()
        current = psu.measurement.current()
        print(f"Measured: {voltage:.2f}V, {current:.3f}A")

        # Disable output
        psu.output.state_set(False)
        print("Output disabled.")

        # Close connection
        psu.close()
        print("Connection closed successfully.")

    except Exception as e:
        print(f"Error: {e}")
        print("This might be due to:")
        print("1. Instrument not connected")
        print("2. Wrong VISA address")
        print("3. PyVISA not installed")
        print("4. Instrument not powered on")


if __name__ == "__main__":
    main()