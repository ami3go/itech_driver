# Release and integration gate (#77)

Status: NOT READY FOR RELEASE. PRs #1–#6 and the review backlog are separate from physical support claims. The original migration is merged; subsequent branches are proposals until verified on an integrated head. The manifest in release_backlog.json tracks #7–#76; #77 is this release gate. PRs #135/#137 are superseded; never merge those duplicates. Recheck current PR states/head SHA before integration.

## Integration procedure

1. Freeze main/master commit, all selected PR head/base SHAs, workflow results and core dependency. Do not merge on stale green checks. Inspect overlapping changes and actual base relationships; stacked PRs need ordered integration. Prefer an isolated integration branch and retain source PRs for audit. Resolve conflicts semantically rather than choosing one entire file. Do not run physical tests.
2. Merge/reconcile communication stack #2–#6; source/output #79–#86, #98, #103, #107–#108, #112–#114, #126–#127, #134; trigger/ARB/battery/system/status/IO corrections #87–#97, #99–#102, #104, #115, #124, #141. Reconcile measurement/identity/logging chain #105–#106, #109–#111, #116, #122–#123, #125 and #129–#140 (exclude superseded #135/#137). ARB offline planning #117–#121/#128 remains offline. Architecture #142–#146 adds supervised operations and offline qualification tooling.
3. Explicitly reconcile shared files: BaseInstrument (logging/error queue/framing/cleanup), ITM3900D constructor (all subsystem wiring and remote session state), factory and identity (exact allowlist), SourceSubsystem and OutputSubsystem (range guards, OPP vs operating limit, watchdog), SystemSubsystem (remote mode, LAN, beeper), test_driver.py and all simulator fixtures (updated command strings and queries).
4. Regenerate #78 command registry after integration for all public methods, including new modules and intentionally unsupported commands. Verify each command against the complete guide V1.4/09,2024 or actual revision. Record page and response/range semantics; do not infer missing syntax. Reconcile nominal ratings and live bounds, avoid hardcoded application profile limits. Close upstream VISA cleanup blocker only after verified core pin update.
5. Run complete offline CI on the exact integrated commit: Windows and Linux Python 3.10/3.13, pytest collection and execution, property/fault/loopback/VISA-sim tests, compileall, build wheel, clean minimal install, pip check, version equality, coverage and regression mutation evidence. Recheck no physical I/O. Record logs and JUnit files, no claims from isolated branch results.
6. Independent code review: verify no replay, explicit remote state, fail-closed model selection, output/protection lifecycle, no false safety claims, acquisition readiness and error queue behavior. Resolve all P0 findings before release. A simulator test does not prove physical behavior.
7. Apply #75 per-command qualification and #76 performance evidence. HIL is NOT RUN; all physical interface/firmware claims remain unqualified. Restrict release scope to verified capabilities; do not publish a hardware-qualified release before passing required physical evidence. Review documentation and tag only after all relevant gates pass.

## Compatibility / capability boundaries

- Python >=3.10; core commit pin; package metadata is version source. VISA, serial and discovery are optional extras. Native TCP does not require VISA. USB VCP parameters explicit. Actual device-interface support not HIL-qualified.
- Model recognition uses exact rated-model list; unknown devices use generic identification/IEEE commands, not ITECH-specific controls.
- Session close does not turn output off. Requested mode/output is not physical state. Explicit supervised operations never guarantee electrical isolation. Protection clear, reset and restore-on-startup are explicit operations.
- Fresh MEAS and buffered FETC are distinct; binary decoder capabilities do not prove device encoding. Native ARB planners are offline only until full guide, readback and execution verification. Logging stop and battery execution remain unsupported. Parallel topology validation is offline.
- No physical instrument authorization needed for simulation; ordinary CI must never contact a bench.

## Offline example (only on branch containing #143)

```python
from itech_driver import ITM3900D
from itech_driver.simulator import ItechSimulator

sim = ItechSimulator()
with ITM3900D("sim", transport=sim.transport) as driver:
    print(driver.identify())
    print(driver.query_scpi("MEAS:VOLT?"))
```

Expected simulated voltage is 0.0. The example neither opens a network resource nor energizes hardware.

## Release evidence checklist

- [ ] Complete integrated PR/issue mapping and exact commit hashes
- [ ] Full command inventory, guide page references and explicit unsupported flags
- [ ] Integrated CI success and artifacts, clean wheel and metadata check
- [ ] Independent safety, capability and compatibility review
- [ ] Actual model/firmware/interface qualification evidence and approved scope
- [ ] Actual timing, acquisition accuracy and soak evidence for claimed features
- [ ] Release notes and examples match integrated implementation, version and limitations

No release/tag has been created by this PR.
