# ITECH-REF-AUTO-01 progress tracker

2026-11-24. All 40 issues individually read. Baseline d0174d457d208d0e9ce84f7463c080c7b7582994; pinned core 1e03b6837f96f200dc28233490639f2f080e1791. Merged source PR #192, master a4e05a4acc4f7b6cd852d0a99ac739f2052605be; candidate 097a6dd19b71829f5fd21699d4d051e9e52f15f0, tree 176343b85403480fd763695a2c250b7526ab22e9. [Original failing run](https://github.com/ami3go/itech_driver/actions/runs/45374107472): 557 passed, 4 failed, 2 deselected (Linux 3.13). [Corrected integrated run](https://github.com/ami3go/itech_driver/actions/runs/45376432340): 563 passed, 2 deselected, all four platforms green and wheels built. [Direct CI](https://github.com/ami3go/itech_driver/actions/runs/45377304624), [clean wheel](https://github.com/ami3go/itech_driver/actions/runs/45377304617), [native TCP](https://github.com/ami3go/itech_driver/actions/runs/45377304657) green. No HIL. No independent local full-clone test (GitHub DNS unavailable).

74 earlier implementation heads consolidated in #192; this does not prove each issue's acceptance. The overlap column is historical PR attribution, not proof of completeness. #187–189 individually commented and closed. #186 remains open for explicit added-method coverage/semantic review. #191 and #193 reconciled with integrated master; new CI pending at recording time.

| Issue | Task | Preliminary state | Candidate/overlap | Remaining verification |
|---|---|---|---|---|
| [#186](https://github.com/ami3go/itech_driver/issues/186) | Registry completeness | PARTIALLY IMPLEMENTED | #78 #190 #192 | Exact-set test green; explicit new-method regression/alias and guide audit pending |
| [#187](https://github.com/ami3go/itech_driver/issues/187) | Remote preflight/framing | VERIFIED AND MERGED | #5 #132 #134 #190 #192 | Guard before MIN/MAX; exact fixture and fragmented reply |
| [#188](https://github.com/ami3go/itech_driver/issues/188) | Remote generation | VERIFIED AND MERGED | #5 #132 #190 #192 | Guard before I/O after reconnect; invalidation on failed range read |
| [#189](https://github.com/ami3go/itech_driver/issues/189) | Failed remote/fault | VERIFIED AND MERGED | #5 #142 #190 #192 | Fault preserved; no output writes or replay; explicit reconnect |
| [#169](https://github.com/ami3go/itech_driver/issues/169) | Exact identity | IMPLEMENTED BUT UNVERIFIED | #130 #106 | Verify exact aliases and malformed identity |
| [#170](https://github.com/ami3go/itech_driver/issues/170) | Generic controls | PARTIALLY IMPLEMENTED | #131 | Verify exposure restriction, not just capability reporting |
| [#171](https://github.com/ami3go/itech_driver/issues/171) | Capability states | PARTIALLY IMPLEMENTED | #131 | Check all four states and no speculative I/O |
| [#172](https://github.com/ami3go/itech_driver/issues/172) | Identity cache | PARTIALLY IMPLEMENTED | #129 #130 | Core parser and generation-aware immutable cache audit |
| [#173](https://github.com/ami3go/itech_driver/issues/173) | Model descriptors | PARTIALLY IMPLEMENTED | #106 #130 #131 | Bind capabilities to subsystem guards |
| [#150](https://github.com/ami3go/itech_driver/issues/150) | Electrical limits | PARTIALLY IMPLEMENTED | #106 #107 #134 #193 | Remove fallback configuration; intersect ranges |
| [#153](https://github.com/ami3go/itech_driver/issues/153) | Nested defaults | IMPLEMENTED IN OPEN PR | #193 | Independent config isolation |
| [#154](https://github.com/ami3go/itech_driver/issues/154) | Configuration persistence | IMPLEMENTED IN OPEN PR | #193 | Path/schema/atomic save |
| [#151](https://github.com/ami3go/itech_driver/issues/151) | Range/channel validation | PARTIALLY IMPLEMENTED | #80 #81 #106 #107 #134 | Remove legacy defaults; centralize |
| [#152](https://github.com/ami3go/itech_driver/issues/152) | Source validation | PARTIALLY IMPLEMENTED | #80 #82 #85 #106 #107 #134 | Protection and application constraints |
| [#155](https://github.com/ami3go/itech_driver/issues/155) | Strict output enable | IMPLEMENTED BUT UNVERIFIED | #81 #142 | Verify all acceptance cases and zero writes |
| [#167](https://github.com/ami3go/itech_driver/issues/167) | Exact ARB integers | PARTIALLY IMPLEMENTED | #88 #118 #119 #120 #121 #128 | Audit raw ARB APIs |
| [#166](https://github.com/ami3go/itech_driver/issues/166) | Strict boolean parse | IMPLEMENTED BUT UNVERIFIED | #104 | Verify malformed state matrix |
| [#156](https://github.com/ami3go/itech_driver/issues/156) | Connection factory | PARTIALLY IMPLEMENTED | #2 #3 #4 #132 | Separate config and selection |
| [#157](https://github.com/ami3go/itech_driver/issues/157) | Optional VISA selection | IMPLEMENTED BUT UNVERIFIED | #2 #3 #136 | Verify installed-wheel and selection |
| [#158](https://github.com/ami3go/itech_driver/issues/158) | CLI discovery | PARTIALLY IMPLEMENTED | #4 #6 | CLI and ownership audit |
| [#159](https://github.com/ami3go/itech_driver/issues/159) | Detection ownership | PARTIALLY IMPLEMENTED | #129 #130 #133 | Single ownership/non-reopenable transport |
| [#160](https://github.com/ami3go/itech_driver/issues/160) | Cleanup exceptions | IMPLEMENTED BUT UNVERIFIED | #133 | Verify double close/foreign manager |
| [#161](https://github.com/ami3go/itech_driver/issues/161) | Independent framing | PARTIALLY IMPLEMENTED | #132 #2 #3 #5 | Asymmetric framing and binary-following query |
| [#168](https://github.com/ami3go/itech_driver/issues/168) | Command registry/executor | PARTIALLY IMPLEMENTED | #78 #190 | Typed semantics and runtime enforcement not complete |
| [#162](https://github.com/ami3go/itech_driver/issues/162) | Source mode aliases | IMPLEMENTED BUT UNVERIFIED | #98 | Canonical delegation observed in #134 source; registry parity pending |
| [#163](https://github.com/ami3go/itech_driver/issues/163) | ARB command ownership | PARTIALLY IMPLEMENTED | #144 | Canonical initiate/abort aliases |
| [#164](https://github.com/ami3go/itech_driver/issues/164) | Core IEEE delegation | NOT STARTED | — | Audit shared Ieee4882 contracts |
| [#165](https://github.com/ami3go/itech_driver/issues/165) | IEEE status ownership | PARTIALLY IMPLEMENTED | #84 #115 | Unify event/status semantics |
| [#174](https://github.com/ami3go/itech_driver/issues/174) | Watchdog sequence | IMPLEMENTED BUT UNVERIFIED | #103 #142 | Verify order and fault tests |
| [#175](https://github.com/ami3go/itech_driver/issues/175) | Acquisition serialization | PARTIALLY IMPLEMENTED | #93 #89 | Concurrent sequence/deadline coverage |
| [#176](https://github.com/ami3go/itech_driver/issues/176) | ARB lifecycle | IMPLEMENTED BUT UNVERIFIED | #144 #142 | Verify cancellation/abort/fault gates |
| [#177](https://github.com/ami3go/itech_driver/issues/177) | Retry removal | PARTIALLY IMPLEMENTED | #84 | Legacy decorator and call sites |
| [#178](https://github.com/ami3go/itech_driver/issues/178) | Supervised CLI | PARTIALLY IMPLEMENTED | #142 #134 #5 | CLI wiring and unknown outcome |
| [#179](https://github.com/ami3go/itech_driver/issues/179) | Bounded completion | PARTIALLY IMPLEMENTED | #144 | Legacy delay budget |
| [#180](https://github.com/ami3go/itech_driver/issues/180) | Optional dependencies | IMPLEMENTED BUT UNVERIFIED | #136 #2 #3 | Optional extras clean-wheel verification |
| [#181](https://github.com/ami3go/itech_driver/issues/181) | Version metadata | IMPLEMENTED BUT UNVERIFIED | #138 | Installed wheel and fallback |
| [#182](https://github.com/ami3go/itech_driver/issues/182) | Legacy VISA example | NOT STARTED | #140 related | Inspect example and imports; #140 is subsystem cleanup |
| [#183](https://github.com/ami3go/itech_driver/issues/183) | Logging import | IMPLEMENTED IN OPEN PR | #191 | Inspect undefined annotation |
| [#184](https://github.com/ami3go/itech_driver/issues/184) | Logging resources | IMPLEMENTED IN OPEN PR | #191 | Owned handlers and Windows rename |
| [#185](https://github.com/ami3go/itech_driver/issues/185) | Static analysis/wheel CI | PARTIALLY IMPLEMENTED | #136 #149 #190 | Static analysis and integrated wheel gate |

Continue in dependency order. No physical access without HIL authorization.
