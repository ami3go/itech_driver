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

## Configuration update

PR #193 merged at a16b25c946acd3bece1ed10fc1a71e45f612710b after reconciled head f24e112de57049e7dbb86d6daa70e0d5dced2a37 passed [offline CI](https://github.com/ami3go/itech_driver/actions/runs/45377662064), [clean wheel](https://github.com/ami3go/itech_driver/actions/runs/45377662096) and native TCP without VISA (run 45377662210). #153 and #154 verified and closed; #150 partial (effective-limit intersection remains). #191 previously passed integrated offline and minimal wheel runs 45377644599/45377644827; reconciled again with #193 at d49ebd1c09c2a0426673763ff32f00541648631b; current CI 45378132484/45378132554 pending at time of recording.
