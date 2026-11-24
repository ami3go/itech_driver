# SCPI core migration and qualification

Baseline ITECH: 66160cf09f11fed95698a7ad05969bbe54f81d9b.
Core: 1e03b6837f96f200dc28233490639f2f080e1791 (0.1.0.dev12).

## Architecture

Public driver/subsystems → BaseInstrument → ScpiSession / ScpiClient →
ScpiTextCodec and core byte transport → VisaTransport or injected scripted transport.

Vendor SCPI syntax, model limits, protection, ARB and battery semantics remain
in the concrete driver. No physical limits are inferred from existing unused
configuration defaults. This migration does not qualify the existing SCPI
command catalogue or introduce a hardware safety envelope.

## Verification gates

- Offline: install/build, compile, exact command checks through all subsystems,
  timeout/no-replay, lifecycle, typed response rejection, binary blocks,
  Hypothesis binary round-trip and real core VisaTransport + PyVISA-sim.
- CI: Linux and Windows, Python 3.10 and 3.13; bounded tests, no bench address.
- Follow-up: exhaustive vendor manual command cross-reference, remaining
  subsystem cases, serial/socket framing, binary missing-terminator behavior,
  resource-specific options, error queue policy, concurrent compound subsystem
  procedures, device-specific capabilities and limits, and physical HIL.
- Physical HIL: not run by default. Obtain explicit bench authorization before
  connecting to real hardware; verify identity/model/ratings and independent
  output safety. First execute read-only IDN/status/setpoint queries. Energized
  tests and protection/ARB/battery procedures require a separate approved
  procedure, known safe load and limits, and operator supervision. Never infer
  safe physical output from simulator results or a disconnected session.

## Evidence

The checked-in fixtures describe expected legacy command strings, not measured
instrument behavior. CI results must be collected on the exact PR head before
claiming a passing offline suite. Physical HIL and command catalogue validation
remain separate acceptance gates.
