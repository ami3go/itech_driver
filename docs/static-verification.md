# Static and installed-wheel verification

Static checks run on Windows and Linux with Python 3.10, 3.11, 3.12 and 3.13.
Ruff F821/F822/F823 checks undefined names, exports and local variables across
the whole package. Mypy is deliberately scoped to the fully annotated identity
and logging API modules; this is not a claim of full-package strict typing.
Public imports are enumerated with pkgutil and imported in each matrix job.
The separate installed-wheel gate runs outside the source tree in a fresh
virtual environment, first with no optional transports, then with discovery
extras and PyVISA-sim. It checks CLI help, simulator behavior, USBTMC/VISA-LAN
simulated read-only identity/output queries, and pyserial loopback. Existing
native TCP loopback and offline regression gates are retained. No physical
instrument, subnet scan, or hardware marker is executed.
