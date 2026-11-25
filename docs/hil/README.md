# ITECH-HIL-RUNBOOK-001 — incremental implementation (NOT READY)

This branch extends the existing qualification gate, not a competing framework.
Baseline ba0898c218109675553daabac215d759f1d27fd3; core 34b0d750558de628349160150091f1fd45badf76.
No physical access or qualification evidence during development.

- [Master runbook](HIL_MASTER_RUNBOOK.md)
- [SCPI traceability inventory](HIL_SCPI_TRACEABILITY.md)
- [Machine-readable work inventory](test_matrix.json)
- [Issue traceability](HIL_ISSUE_TRACEABILITY.md)
- Existing [manifest gate](../qualification_manifest.md), [physical gate](../physical_qualification_gate.md), [interface guide](../interface-qualification.md) and [performance evidence](../performance_qualification.md) remain authoritative for evidence requirements. Legacy direct hardware commands now additionally require a scoped permit and bench configuration; use the new runner.

A dedicated optional HIL dependency provides Ed25519 permit verification. The operator retains the encrypted private key; the runner reads only the trusted public key.

Only two existing communication test procedures are connected to the runner.
The communication suite includes unresolved discovery and recovery items, so it intentionally refuses execution; select an individual implemented test.
This is not a production qualification or a complete executable HIL campaign.
