# Offline regression tests

Install with `python -m pip install -e '.[dev]'`, then run `python -m pytest --collect-only -q` and `python -m pytest --junitxml=interface-results.xml`. Pytest's no-tests-collected exit status is nonzero, as are failed assertions. The configured testpaths is `tests`; the hardware marker is excluded by default. Ordinary CI runs this suite on Windows/Linux Python 3.10/3.13 and uploads JUnit evidence. Use injected core ScriptedScpiTransport, VISA-sim and local loopback only. Do not run physical tests without separately approved HIL access.

The former root test.py contained only commented examples, including an output enable command, and was removed. Regression assertions live in tests/test_driver.py and subsystem-specific suites. A mutation of the emitted command, parser, or no-replay behavior must fail the relevant golden/failure regression. Formal mutation execution across the integrated branch remains part of final qualification.
