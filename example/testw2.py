#!/usr/bin/env python3
"""
ITECH IT-M3900D Power Supply Example Usage

This script demonstrates how to use the IT-M3900D power supply driver
for various operations including basic control, measurements, and error handling.

Replace the resource string with your actual instrument's VISA address.
"""

import time
from itech_driver import create_instrument, auto_detect_instrument, ITM3900D


def basic_operations_example(resource_string):
    """Demonstrate basic power supply operations."""
    print("=" * 60)
    print("BASIC OPERATIONS EXAMPLE")
    print("=" * 60)

    try:
        # Create instrument instance
        print(f"Connecting to {resource_string}...")
        psu = create_instrument('IT-M3900D', resource_string)

        # Identify the instrument
        idn = psu.identify()
        print(f"Connected to: {idn}")

        # Get detailed model information
        if hasattr(psu, 'get_model_info'):
            model_info = psu.get_model_info()
            print(f"Manufacturer: {model_info['manufacturer']}")
            print(f"Model: {model_info['model']}")
            print(f"Serial: {model_info['serial']}")
            print(f"Firmware: {model_info['firmware']}")

        # Reset to default settings
        print("\nResetting to default settings...")
        psu.reset()
        time.sleep(1)  # Wait for reset to complete

        # Set voltage and current limits
        print("\nSetting voltage to 5.0V and current limit to 1.0A...")
        psu.source.voltage_set(5.0)
        psu.source.current_set(1.0)

        # Enable output
        print("Enabling output...")
        psu.output.state_set(True)

        # Wait a bit for stability
        time.sleep(2)

        # Read back settings
        actual_voltage = psu.source.voltage_query()
        actual_current = psu.source.current_query()
        output_state = psu.output.state_query()

        print(f"Set voltage: 5.0V, Actual voltage: {actual_voltage:.3f}V")
        print(f"Set current: 1.0A, Actual current limit: {actual_current:.3f}A")
        print(f"Output state: {'ON' if output_state else 'OFF'}")

        # Take measurements
        print("\nTaking measurements...")
        measured_voltage = psu.measurement.voltage()
        measured_current = psu.measurement.current()
        measured_power = psu.measurement.power()

        print(f"Measured voltage: {measured_voltage:.3f}V")
        print(f"Measured current: {measured_current:.3f}A")
        print(f"Measured power: {measured_power:.3f}W")

        # Disable output
        print("\nDisabling output...")
        psu.output.state_set(False)

        # Close connection
        psu.close()
        print("Connection closed.")

    except Exception as e:
        print(f"Error during basic operations: {e}")
        raise


def protection_settings_example(resource_string):
    """Demonstrate protection settings."""
    print("\n" + "=" * 60)
    print("PROTECTION SETTINGS EXAMPLE")
    print("=" * 60)

    try:
        psu = create_instrument('IT-M3900D', resource_string)

        # Set protection levels
        print("Setting over-voltage protection to 6.0V...")
        psu.source.ovp_set(6.0)

        print("Setting over-current protection to 1.2A...")
        psu.source.ocp_set(1.2)

        # Enable protections
        print("Enabling OVP and OCP...")
        psu.source.ovp_enable(True)
        psu.source.ocp_enable(True)

        # Read back protection settings
        ovp_level = psu.source.ovp_query()
        ocp_level = psu.source.ocp_query()
        ovp_enabled = psu.source.ovp_enable_query()
        ocp_enabled = psu.source.ocp_enable_query()

        print(f"OVP level: {ovp_level:.2f}V, Enabled: {ovp_enabled}")
        print(f"OCP level: {ocp_level:.2f}A, Enabled: {ocp_enabled}")

        # Check protection status (if supported)
        if hasattr(psu, 'get_protection_status'):
            status = psu.get_protection_status()
            print("Protection status:")
            for protection, active in status.items():
                print(f"  {protection.upper()}: {'ACTIVE' if active else 'OK'}")

        psu.close()

    except Exception as e:
        print(f"Error during protection settings: {e}")


def system_commands_example(resource_string):
    """Demonstrate system commands."""
    print("\n" + "=" * 60)
    print("SYSTEM COMMANDS EXAMPLE")
    print("=" * 60)

    try:
        psu = create_instrument('IT-M3900D', resource_string)

        # Check for errors
        error = psu.system.error()
        print(f"System error status: {error}")

        # Clear any errors
        psu.system.clear()
        print("System status cleared.")

        # Set remote control mode
        psu.system.remote()
        print("Set to remote control mode.")

        # Check system version
        version = psu.system.version()
        print(f"System version: {version}")

        psu.close()

    except Exception as e:
        print(f"Error during system commands: {e}")


def auto_detection_example(resource_string):
    """Demonstrate auto-detection feature."""
    print("\n" + "=" * 60)
    print("AUTO-DETECTION EXAMPLE")
    print("=" * 60)

    try:
        print("Attempting auto-detection...")
        psu = auto_detect_instrument(resource_string)

        idn = psu.identify()
        print(f"Auto-detected instrument: {idn}")

        # Check what type of instrument we got
        if isinstance(psu, ITM3900D):
            print("Successfully detected IT-M3900D series!")
            # Perform IT-M3900D specific operations
            psu.source.voltage_set(3.3)
            print(f"Set voltage to 3.3V for demonstration")
        else:
            print("Using generic SCPI instrument interface")
            # Use generic commands
            psu.source.voltage_set(5.0)
            print(f"Set voltage to 5.0V using generic interface")

        psu.output.state_set(False)  # Ensure output is off
        psu.close()

    except Exception as e:
        print(f"Error during auto-detection: {e}")


def error_handling_example(resource_string):
    """Demonstrate error handling."""
    print("\n" + "=" * 60)
    print("ERROR HANDLING EXAMPLE")
    print("=" * 60)

    try:
        psu = create_instrument('IT-M3900D', resource_string)

        # Try an invalid command to demonstrate error handling
        print("Testing error handling with invalid command...")
        try:
            # This command might not exist and should raise an error
            psu.write_scpi('INVALID:COMMAND')
        except Exception as e:
            print(f"Command error caught: {e}")

        # Check system error after the invalid command
        error = psu.system.error()
        print(f"System error after invalid command: {error}")

        # Clear the error
        psu.system.clear()
        print("Errors cleared.")

        psu.close()

    except Exception as e:
        print(f"Error during error handling demo: {e}")


def comprehensive_example(resource_string):
    """Comprehensive example showing multiple operations."""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE EXAMPLE")
    print("=" * 60)

    try:
        psu = create_instrument('IT-M3900D', resource_string)

        print(f"Instrument: {psu.identify()}")

        # Configuration sequence
        print("\n1. Configuration:")
        psu.source.voltage_set(12.0)
        psu.source.current_set(0.5)
        psu.source.ovp_set(13.0)
        psu.source.ocp_set(0.6)

        print(f"   Voltage set to: 12.0V")
        print(f"   Current limit set to: 0.5A")
        print(f"   OVP set to: 13.0V")
        print(f"   OCP set to: 0.6A")

        # Verification
        print("\n2. Verification:")
        actual_voltage = psu.source.voltage_query()
        actual_current = psu.source.current_query()
        print(f"   Actual voltage: {actual_voltage:.2f}V")
        print(f"   Actual current limit: {actual_current:.2f}A")

        # Operation
        print("\n3. Operation:")
        psu.output.state_set(True)
        print("   Output enabled")

        # Monitoring
        print("\n4. Monitoring (5 seconds):")
        for i in range(5):
            voltage = psu.measurement.voltage()
            current = psu.measurement.current()
            power = psu.measurement.power()
            print(f"   {i + 1}s: {voltage:.2f}V, {current:.3f}A, {power:.2f}W")
            time.sleep(1)

        # Shutdown
        print("\n5. Shutdown:")
        psu.output.state_set(False)
        print("   Output disabled")

        psu.close()
        print("   Connection closed")

    except Exception as e:
        print(f"Error in comprehensive example: {e}")
        raise


def main():
    """Main function to run all examples."""
    # Replace this with your actual instrument's VISA address
    # Common examples:
    # - 'TCPIP0::192.168.1.100::inst0::INSTR'  # LAN connection
    # - 'USB0::0x1234::0x5678::0123456789::INSTR'  # USB connection
    # - 'GPIB0::12::INSTR'  # GPIB connection
    # - 'ASRL1::INSTR'  # Serial connection

    resource_string = 'TCPIP0::192.168.1.100::inst0::INSTR'  # Change this!

    print("ITECH IT-M3900D Power Supply Driver Examples")
    print("=" * 60)
    print(f"Using resource string: {resource_string}")
    print("Note: Replace with your actual instrument's address")
    print("=" * 60)

    try:
        # Run examples
        basic_operations_example(resource_string)
        protection_settings_example(resource_string)
        system_commands_example(resource_string)
        auto_detection_example(resource_string)
        error_handling_example(resource_string)
        comprehensive_example(resource_string)

        print("\n" + "=" * 60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        print("This is likely because:")
        print("1. The instrument is not connected")
        print("2. The VISA address is incorrect")
        print("3. PyVISA is not installed properly")
        print("4. The instrument is not powered on")
        print("\nPlease check your setup and try again.")


if __name__ == "__main__":
    main()