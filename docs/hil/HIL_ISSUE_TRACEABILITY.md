# Issue traceability — initial snapshot

Baseline ba0898c218109675553daabac215d759f1d27fd3. Direct issue queries found all four remaining campaign issues open.
The integrated report in ../refactoring/ITECH_REF_FINAL_REPORT.md is interim;
reconcile every #150–189 issue with live issue state and exact CI before closure.

| Issue | Existing code / offline evidence paths | Physical work | Status |
|---|---|---|---|
| #152 | docs/protection-threshold-qualification.md; tests/test_effective_setpoint_enforcement.py; tests/test_protection_qualification.py | HIL-SRC/HIL-PROT: exact model/firmware bounds, invalid writes rejected, separate bounded trip tests | OPEN/BLOCKED |
| #167 | docs/arb-integer-qualification.md; tests/test_arb_exact_integers.py; tests/test_arb_integer_qualification.py | HIL-ARB: command-specific integer bounds and physical repeat verification | OPEN/BLOCKED |
| #168 | docs/runtime-registry-disposition.md; tests/test_complete_runtime_registry.py | HIL-PG: authoritative command/range/response mapping; no duplicate definitions | OPEN/BLOCKED |
| #173 | docs/method-qualification.md; tests/test_model_descriptors.py; tests/test_method_qualification.py | HIL-MODEL: exact firmware/model/interface applicability and no-I/O rejection | OPEN/BLOCKED |
| #75 / PR #145, #148 | existing manifest/evidence gate integrated on baseline | HIL-PG plus all required physical cases | physical NOT RUN; reconcile open PRs |
| #76 / PR #146 | existing performance evidence module | HIL-PERF/HIL-SOAK24 | physical NOT RUN |
| #77 / PR #147 | release gate | complete mandatory matrix | NOT READY |

No issues closed by this increment. Existing tests listed are source paths,
not newly executed results. Other campaign issues require individual review.
