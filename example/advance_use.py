"""Advanced usage examples for the power supply driver."""

from itech_driver import (
    create_instrument,
    auto_detect_instrument,
    list_available_instruments,
    register_instrument
)


def demonstrate_factory_functions():
    """Demonstrate the various factory functions."""
    print("Available instrument models:", list_available_instruments())

    # Method 1: Create specific instrument
    print("\n1. Creating specific IT-M3900D instrument...")
    try:
        psu1 = create_instrument('IT-M3900D', 'TCPIP0::192.168.1.50::inst0::INSTR')
        print(f"   Created: {psu1.identify()}")
        psu1.close()
    except Exception as e:
        print(f"   Error: {e}")

    # Method 2: Auto-detection
    print("\n2. Auto-detecting instrument...")
    try:
        psu2 = auto_detect_instrument('TCPIP0::192.168.1.50::inst0::INSTR')
        info = psu2.get_instrument_info() if hasattr(psu2, 'get_instrument_info') else {}
        print(f"   Detected: {psu2.identify()}")
        print(f"   Instrument info: {info}")
        psu2.close()
    except Exception as e:
        print(f"   Error: {e}")

    # Method 3: Using generic instrument
    print("\n3. Creating generic instrument...")
    try:
        psu3 = create_instrument('Generic', 'TCPIP0::192.168.1.50::inst0::INSTR')
        print(f"   Generic instrument created")

        # Test basic functionality
        capabilities = psu3.detect_capabilities() if hasattr(psu3, 'detect_capabilities') else {}
        print(f"   Capabilities: {capabilities}")

        psu3.close()
    except Exception as e:
        print(f"   Error: {e}")


def demonstrate_instrument_management():
    """Demonstrate instrument management features."""
    print("\n--- Instrument Management ---")

    # List available instruments
    print("Supported models:", list_available_instruments())

    # Example of registering a new instrument type
    print("\nRegistering a new instrument type...")

    # This would typically be done in your instrument implementation file
    # from .instruments.it6900 import IT6900Series
    # register_instrument('IT6900', IT6900Series)

    print("New models would be registered using register_instrument()")


if __name__ == '__main__':
    print("Advanced Power Supply Driver Examples")
    print("=====================================")

    demonstrate_factory_functions()
    demonstrate_instrument_management()

    print("\nNote: These examples assume instruments are available at the specified addresses.")
    print("Replace the resource strings with actual instrument addresses for real usage.")