# ITECH refactoring verification — interim

Baseline d0174d457d208d0e9ce84f7463c080c7b7582994; pinned core 1e03b6837f96f200dc28233490639f2f080e1791. Merged source PR #192, master a4e05a4acc4f7b6cd852d0a99ac739f2052605be; candidate 097a6dd19b71829f5fd21699d4d051e9e52f15f0, tree 176343b85403480fd763695a2c250b7526ab22e9. [Original failing run](https://github.com/ami3go/itech_driver/actions/runs/45374107472): 557 passed, 4 failed, 2 deselected (Linux 3.13). [Corrected integrated run](https://github.com/ami3go/itech_driver/actions/runs/45376432340): 563 passed, 2 deselected, all four platforms green and wheels built. [Direct CI](https://github.com/ami3go/itech_driver/actions/runs/45377304624), [clean wheel](https://github.com/ami3go/itech_driver/actions/runs/45377304617), [native TCP](https://github.com/ami3go/itech_driver/actions/runs/45377304657) green. No HIL. No independent local full-clone test (GitHub DNS unavailable).

## Issue-level tests

#186: tests/test_command_registry.py::test_subsystem_registry_covers_public_methods passed exact set and uniqueness; explicit new-method regression pending.

#187: tests/test_remote_mode.py::test_remote_guard_and_context_order; test_fragmented_range_reply_preserves_exact_order; test_missing_range_terminator_invalidates_remote_authorization. No sleeps or timeout suppression.

#188: test_system_methods_and_generation; missing-range-terminator test. Generation changes and failed read invalidate authorization.

#189: test_failed_remote_never_enables_guard. Original timeout, FAULTED, no replay/activation, reconnect without permission.

#191 logging: isolated local Linux 3.13 2 tests pass; initial four-platform CI run 45377072989 green before consolidation. Reconciled head db466bb058b452c53322fc3967d0544f384ccefa; [new CI](https://github.com/ami3go/itech_driver/actions/runs/45377644599) pending at recording time.

#193 config: isolated local Linux 3.13 14 tests pass; reconciled head f24e112de57049e7dbb86d6daa70e0d5dced2a37; [new CI](https://github.com/ami3go/itech_driver/actions/runs/45377662064) pending at recording time.

## Guide and HIL boundary

No new wire syntax introduced in phase-1 production change; fixture uses existing SYST:REM, SYST:LOC and SOUR:VOLT? MIN/MAX and SOUR:VOLT command forms. Programming guide revision, page-specific argument/response/model and firmware verification remain unconfirmed. Do not mark inventory entries guide_verified. Physical remote request, output/protection status, ratings/range accuracy, interfaces and ARB timing/abort must be verified using approved HIL procedure. Offline simulation does not establish actual physical execution. Record instrument IDN, firmware, interface, exact guide revision, source/core commits, command/response trace, and independent measurement where applicable. Do not energize without authorized bench procedure.

Coverage/static lint/type gates and every issue-specific acceptance still require individual audit; no fabricated coverage figure.
