# ITECH IT-M3900D Python driver

ITECH IT-M3900D high-power DC supply command wrappers using
[scpi-driver-core](https://github.com/ami3go/scpi-driver-core).

Python 3.10+. Install with `python -m pip install -e '.[test]'` from a clone.
The dependency is pinned to a reviewed core commit; Git and GitHub access are required.
VISA is optional: install `.[visa]` for VISA resources, `.[serial]` for VCP,
or `.[discovery]` for discovery extras. Native TCP and the injected simulator
require neither PyVISA nor pyserial. Tests use only local simulators/loopback.
The installed distribution metadata is the sole release version source;
a bare source tree with dependencies available but no installed driver
metadata reports `0+unknown` rather than an invented release number.
Install the project (editable or wheel) to obtain the authoritative version.

## Public API

```python
from itech_driver import ITM3900D

# Replace with the verified instrument resource. Opening does not energize output.
with ITM3900D("TCPIP0::192.0.2.10::inst0::INSTR", timeout=5000) as psu:
    print(psu.identify())
    print(psu.source.voltage_query())
    print(psu.session.health)
```

Existing factory functions and all 11 subsystem interfaces remain. SCPI command
strings are retained from the original driver, not independently hardware-qualified.
Timeout remains milliseconds; it is converted to seconds for the shared core.
Writes and queries are never automatically replayed. Closing the driver releases
its own resource, not the shared VISA manager, and does **not** switch output off.
A communication error does not establish the physical output state.

### Compatibility changes

- Python 3.7–3.9 no longer supported.
- Use `session`, `client`, or `session.transport` rather than raw `visa`.
- Arbitrary legacy `interface_kwargs` are rejected explicitly; use
  `visa_library`, `resource_manager`, `chunk_size`, or inject a configured
  core transport. Serial and VISA socket framing require qualification.
- Numeric and boolean query results use core parsers; malformed and overload
  replies raise instead of silently returning unsafe values.
- Failed auto-detection propagates the original error and closes the connection;
  unknown valid identities use the generic driver.
- Binary queries support definite-length IEEE-488.2 blocks, little endian by
  default, with explicit endian and trailing-terminator options.
- `PowerSupplyError` is the core error root; legacy timeout and communication
  exceptions preserve the original cause.

## Offline testing

```sh
python -m pip install -e '.[test]'
python -m pytest
```

No physical I/O in normal CI. See [migration and qualification notes](docs/migration.md).
