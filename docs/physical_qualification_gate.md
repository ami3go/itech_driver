# Physical programming-guide qualification (#75)

Status: NOT RUN. Normal CI is offline only. Do not execute this plan without separate operator authorization for the specific bench, wiring and test scope. This document does not authorize hardware contact.

## Required identification and prerequisites

Record operator authorization reference, UTC timestamps, driver commit, pinned core commit, model, serial, firmware from raw *IDN?, complete IT-M3900D programming-guide revision and SHA-256, interface (VISA USBTMC, VISA LAN, native TCP, USB VCP as applicable), endpoint/framing, supply ratings, load and wiring, independent reference instrument model/serial/calibration validity. Test each supported model/firmware/interface combination independently. Do not infer support from another model or synthetic simulator.

Operator verifies an accessible emergency disconnect, suitable fusing/current limits, safe load and isolated reference probes, initial output disabled and independently measured residual voltage/current within bench-specific limits. No generic reset, automatic protection clear, output enable, bypass or unattended reconnect. Energized scope must be explicitly approved. Abort/communication loss/unknown state: stop software sequence; operator uses independent safety path, confirms de-energization and records outcome. Never automatically replay a command.

## Matrix groups (expand to every public command/set/query)

| Group | Issues | Required evidence |
|---|---|---|
| ID, transport, remote/local | 11–14,59–63,70 | raw request/response, framing, timeout, ownership, cleanup |
| Output, setpoints, limits | 8–10,15–16,33–38,42–44,64,72 | approved range endpoints, invalid requests, programmed state, independent measured V/I, protection trip and inhibit |
| Trigger, acquisition, fetch | 19–23,39–41,46 | readiness, trigger source, sample count, timebase, raw transfer, malformed/timeout handling |
| ARB native shapes and execution | 17–18,47–51,58,74 | full guide field/range/readback, finite and abort cases, reference waveform, status mapping |
| Battery and logging | 24–25,31–32,52–53,69 | actual execution/stop procedure, storage prerequisites, timestamps and data layout |
| Digital IO, parallel, external analog | 29–30,54–57 | approved topology/wiring, independent electrical observation, option presence and readback |
| System/status | 26–28,34,45 | register semantics, read-to-clear evidence, startup/network changes separately approved |

For each command, capture exact guide page, long/short form, argument units/range, expected response, preconditions and side effects; record raw TX/RX (binary as file), timestamps, error-queue results (destructive read identified), independent reference where relevant, and explicit result. For unsupported syntax do not transmit speculative commands. Record UNKNOWN/NOT_RUN, not PASS. A successful query is not proof of a setter or physical outcome.

## Evidence procedure

1. Populate the per-command inventory from the complete guide; reconcile #71 registry and actual integrated driver. Include omitted guide commands and unsupported capabilities explicitly.
2. Expand each supported command into rows for every claimed model/firmware/interface; set required=true for every release claim. Freeze the expected values/tolerances and safety plan before run.
3. Execute only operator-approved rows with independent measurement. Preserve original transcripts and raw acquisition files; redact credentials only. Record failures; do not overwrite with successful reruns.
4. For each tested row, attach relative evidence file paths and SHA-256 digests. Record separate verified safe-state evidence after energized work, including independent instrument result. Do not mark pass based on readback alone.
5. Run the offline evidence checker with the evidence JSON and artifact directory. PASS from the checker only means structural completeness and matching digests; human review of measurement correctness and coverage is mandatory. A claimed feature cannot ship as physically qualified while any required row is NOT_RUN, FAIL or UNKNOWN.

Run: python -m itech_driver.qualification evidence.json --artifacts evidence_directory

No hardware commands are executed by this checker. The template is intentionally empty and fails the gate.
