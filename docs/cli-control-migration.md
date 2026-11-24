# CLI control migration

Read-only identity is the default; a recognized model also permits reading
setpoints. Setting changes require explicit application voltage/current/power
ceilings and initially OFF readback. The whole request is preflighted before
remote mode and setting writes, and exact numeric setting readback is required
before activation. If a device rounds a setpoint, the CLI fails rather than
silently accepting a mismatch. ON requires --authorize-output, explicit
--hold-seconds and residual limits. It uses the supervised output lifecycle,
requests OFF once on completion or interruption when the same session remains
connected, and verifies residuals. No implicit activation, leave-on mode,
reset, protection disable or automatic reconnect/replay. A failed preflight
does not request ON. If communication fails after ON, the result is UNKNOWN;
the CLI exits nonzero and the operator must use independent bench safety.
Closing the transport is not physical isolation. OFF alone requires residual
limits; do not combine it with setting changes. CLI use is not HIL authorization.
