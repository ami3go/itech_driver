# ITECH refactoring architecture — interim

## Observed baseline and direction

The old master required VISA as a dependency; consolidated master has optional VISA/serial extras and verified native TCP minimal installation. Shared core remains pinned and owns generic transport/session primitives. Vendor methods remain in ITECH subsystems. Registry inventory now matches public subsystem methods; 147 entries added as unverified, not certified command semantics.

## Remote guard invariant

The session lock must span authorization preflight, live range queries, and final write. Guard preflight precedes I/O in compound setpoint setters. Final write guard remains. A fault or changed session generation invalidates requested remote state; no automatic replay, implicit activation or inference of physical output state. Explicit reconnect does not authorize output.

## Remaining design contracts

- Separate exact model/firmware identity, immutable ratings, live ranges, application limits, command-specific constraints, qualification status. Unknown capabilities fail closed. Do not invent ratings. Intersect all applicable constraints.
- One authoritative command registry with typed parameters, parsers, side effects, replay policies, capability and guide references; aliases delegate to canonical operations. Inventory is not yet runtime enforcement.
- Single session ownership across detection and transports, independent framing, bounded operations and deterministic cleanup. Generic functionality must be contributed to core when absent rather than duplicated.
- Explicit lifecycle: arm, trigger, verify, cancel, abort, unknown outcome. Connection status is not output status.
- Config and logging candidates #193/#191 remove shared defaults and improve resource ownership. Effective-limit enforcement remains open.

See progress tracker for issue-level gaps. No physical authorization assumed.
