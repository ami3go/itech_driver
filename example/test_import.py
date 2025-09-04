#!/usr/bin/env python3
"""Simple test to verify auto_detect_instrument import."""

import sys
import os

# Add the src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.abspath(os.path.join(current_dir, 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
    print(f"Added to path: {src_path}")

try:
    # Test 1: Import from main package
    from itech_driver import auto_detect_instrument, create_instrument

    print("✅ Successfully imported from itech_driver")

    # Test 2: Import from instruments module directly
    from itech_driver.instruments import auto_detect_instrument as auto_detect_direct

    print("✅ Successfully imported from itech_driver.instruments")

    # Test 3: Check if they're the same function
    if auto_detect_instrument is auto_detect_direct:
        print("✅ Both imports reference the same function")
    else:
        print("❌ Different function references")

    print(f"Function: {auto_detect_instrument}")
    print(f"Function name: {auto_detect_instrument.__name__}")

except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("Current Python path:")
    for path in sys.path:
        print(f"  {path}")

    # Try to debug what's available
    try:
        import itech_driver

        print("Available in itech_driver:", dir(itech_driver))
    except:
        print("Could not import itech_driver at all")

    try:
        import itech_driver.instruments

        print("Available in instruments:", dir(itech_driver.instruments))
    except:
        print("Could not import instruments module")