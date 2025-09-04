# For example, if your script is in itech_driver/examples/
import sys
import os

from itech_driver import create_instrument
# Method 1: Explicit creation
psu = create_instrument('IT-M3900D', 'TCPIP0::192.168.1.50::inst0::INSTR')

# Method 2: Auto-detection
psu = auto_detect_instrument('TCPIP0::192.168.1.50::inst0::INSTR')

# Use common interface
psu.source.voltage_set(12.0)
psu.output.state_set(True)
print(psu.identify())