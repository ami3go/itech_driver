# ITECH-COM-05 — Interface qualification
Dependencies: COM-01 through COM-04.
## Requirements
- Separate offline qualification for USBTMC, VISA LAN (VXI-11 resource addressing), native raw TCP, USB VCP, discovery and remote-mode semantics.
- Real driver/core stack through PyVISA-sim USB and LAN resources; native TCP loopback; fake serial and pyserial loopback. Simulators do not establish real protocol compatibility with hardware.
- Linux/Windows Python 3.10 and 3.13 CI, no physical hardware by default. JUnit artifacts with per-test outcomes, finite per-test and job budgets.
- Explicit hardware suite with interface, endpoint, expected serial, timeout and authorized operator opt-in. Refuse missing or contradictory config before open. Identify twice, check same expected model/serial and close. Do not transmit setting/output commands.
- Separate manual panel checks and optional remote/local test only after explicit additional operator authorization. Physical output safety and protection/energized tests are outside this read-only run.
- Evidence per interface: model, firmware, serial, backend/version, OS, commit, framing, timeouts, JUnit, observed panel behavior, pass/fail and limitations.
## Acceptance
All offline suites green on exact integrated head. HIL runner must refuse unconfigured invocation, and report each interface separately; no hardware pass without recorded real bench evidence. Full vendor catalogue and energized safety qualification remain independent.
