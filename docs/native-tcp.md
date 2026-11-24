# Native TCP
Install the driver with no extras for standard-library TCP. For existing VISA resources install `.[visa]`; for offline suite install `.[dev]`.
```python
from itech_driver import connect_tcp
with connect_tcp("192.0.2.10", port=30000, timeout=2000) as psu:
    print(psu.identify())
```
Configure LAN socket port on the instrument; LF framing is fixed by the user manual. No output state is changed by opening or closing. The native transport does not implement VXI-11, Telnet or HiSLIP. COM-05 covers physical qualification.
