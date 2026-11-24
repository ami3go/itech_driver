# USB VCP
Install `python -m pip install '.[serial]'`. Select USB VCP in System → I/O → USB; match serial settings. On Windows use the enumerated COM port, on Linux the corresponding /dev/ttyACM* or /dev/ttyUSB* device.
```python
from itech_driver import connect_vcp
with connect_vcp("COM5", baudrate=9600, timeout=2000) as psu:
    print(psu.identify())
```
Defaults: 9600, 8N1, LF, no flow control. CRLF and explicit DTR/RTS are available; check actual firmware settings. USBTMC remains a separate VISA path.
