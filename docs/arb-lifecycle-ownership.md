# ARB lifecycle command ownership
ArbSubsystem.init/abort are compatibility aliases of InitiateSubsystem.arb
and AbortSubsystem.arb. The bounded lifecycle uses the same source, repeat,
init, status, trigger and abort API as low-level callers, with no duplicate
wire commands. Repeat arguments validated before any configuration write.
A trigger and an abort are attempted at most once per owned execution.
Abort readback must map to ABORTED; otherwise the outcome remains UNKNOWN.
Polling has an explicit finite poll budget and per-transaction core timeout;
caller callbacks must return promptly. No status map is supplied for real
firmware without explicit provenance. Simulation states do not qualify
hardware or demonstrate physical output OFF. No automatic reconnect.
