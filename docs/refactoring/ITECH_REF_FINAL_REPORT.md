# ITECH-REF-AUTO-01 final report — INTERIM, campaign not complete

Baseline d0174d457d208d0e9ce84f7463c080c7b7582994; pinned core 1e03b6837f96f200dc28233490639f2f080e1791. Merged source PR #192, master a4e05a4acc4f7b6cd852d0a99ac739f2052605be; candidate 097a6dd19b71829f5fd21699d4d051e9e52f15f0, tree 176343b85403480fd763695a2c250b7526ab22e9. [Original failing run](https://github.com/ami3go/itech_driver/actions/runs/45374107472): 557 passed, 4 failed, 2 deselected (Linux 3.13). [Corrected integrated run](https://github.com/ami3go/itech_driver/actions/runs/45376432340): 563 passed, 2 deselected, all four platforms green and wheels built. [Direct CI](https://github.com/ami3go/itech_driver/actions/runs/45377304624), [clean wheel](https://github.com/ami3go/itech_driver/actions/runs/45377304617), [native TCP](https://github.com/ami3go/itech_driver/actions/runs/45377304657) green. No HIL. No independent local full-clone test (GitHub DNS unavailable).

## Delivered

#192 merged: 74 existing primary PR heads, 139 changed files, four integrated regressions fixed. #187, #188, #189 verified and closed. #186 exact registry inventory test passing but separate added-method regression remains. #191 submitted; #193 subsequently merged, see configuration update below. No HIL.

## All 40 issue dispositions

| Issue | Task | Preliminary state | Candidate/overlap | Remaining verification |
|---|---|---|---|---|
| [#186](https://github.com/ami3go/itech_driver/issues/186) | Registry completeness | VERIFIED AND MERGED | #192 #196 | Issue closed; see continuation evidence |
| [#187](https://github.com/ami3go/itech_driver/issues/187) | Remote preflight/framing | VERIFIED AND MERGED | #192 | Issue closed; see continuation evidence |
| [#188](https://github.com/ami3go/itech_driver/issues/188) | Remote generation | VERIFIED AND MERGED | #192 | Issue closed; see continuation evidence |
| [#189](https://github.com/ami3go/itech_driver/issues/189) | Failed remote/fault | VERIFIED AND MERGED | #192 | Issue closed; see continuation evidence |
| [#169](https://github.com/ami3go/itech_driver/issues/169) | Exact identity | VERIFIED AND MERGED | #195 | Issue closed; see continuation evidence |
| [#170](https://github.com/ami3go/itech_driver/issues/170) | Generic controls | VERIFIED AND MERGED | #192 | Issue closed; see continuation evidence |
| [#171](https://github.com/ami3go/itech_driver/issues/171) | Capability states | PARTIALLY IMPLEMENTED | #131 | #195: four-state model; per-command qualification pending |
| [#172](https://github.com/ami3go/itech_driver/issues/172) | Identity cache | VERIFIED AND MERGED | #197 | Issue closed; see continuation evidence |
| [#173](https://github.com/ami3go/itech_driver/issues/173) | Model descriptors | PARTIALLY IMPLEMENTED | #106 #130 #131 | #195 #198: descriptors and five electrical setters; all subsystem/firmware gates pending |
| [#150](https://github.com/ami3go/itech_driver/issues/150) | Electrical limits | VERIFIED AND MERGED | #193 #195 #198 | Issue closed; see continuation evidence |
| [#153](https://github.com/ami3go/itech_driver/issues/153) | Nested defaults | VERIFIED AND MERGED | #193 | Issue closed; see continuation evidence |
| [#154](https://github.com/ami3go/itech_driver/issues/154) | Configuration persistence | VERIFIED AND MERGED | #193 | Issue closed; see continuation evidence |
| [#151](https://github.com/ami3go/itech_driver/issues/151) | Range/channel validation | PARTIALLY IMPLEMENTED | #80 #81 #106 #107 #134 | Remove legacy defaults; centralize |
| [#152](https://github.com/ami3go/itech_driver/issues/152) | Source validation | PARTIALLY IMPLEMENTED | #80 #82 #85 #106 #107 #134 | #198: effective programmed electrical ranges; protection threshold limits pending |
| [#155](https://github.com/ami3go/itech_driver/issues/155) | Strict output enable | VERIFIED AND MERGED | #196 | Issue closed; see continuation evidence |
| [#167](https://github.com/ami3go/itech_driver/issues/167) | Exact ARB integers | PARTIALLY IMPLEMENTED | #88 #118 #119 #120 #121 #128 | Audit raw ARB APIs |
| [#166](https://github.com/ami3go/itech_driver/issues/166) | Strict boolean parse | VERIFIED AND MERGED | #196 | Issue closed; see continuation evidence |
| [#156](https://github.com/ami3go/itech_driver/issues/156) | Connection factory | PARTIALLY IMPLEMENTED | #2 #3 #4 #132 | Separate config and selection |
| [#157](https://github.com/ami3go/itech_driver/issues/157) | Optional VISA selection | IMPLEMENTED BUT UNVERIFIED | #2 #3 #136 | Verify installed-wheel and selection |
| [#158](https://github.com/ami3go/itech_driver/issues/158) | CLI discovery | PARTIALLY IMPLEMENTED | #4 #6 | CLI and ownership audit |
| [#159](https://github.com/ami3go/itech_driver/issues/159) | Detection ownership | VERIFIED AND MERGED | #199 | Issue closed; see continuation evidence |
| [#160](https://github.com/ami3go/itech_driver/issues/160) | Cleanup exceptions | IMPLEMENTED BUT UNVERIFIED | #133 | Verify double close/foreign manager |
| [#161](https://github.com/ami3go/itech_driver/issues/161) | Independent framing | PARTIALLY IMPLEMENTED | #132 #2 #3 #5 | Asymmetric framing and binary-following query |
| [#168](https://github.com/ami3go/itech_driver/issues/168) | Command registry/executor | PARTIALLY IMPLEMENTED | #78 #190 | Typed semantics and runtime enforcement not complete |
| [#162](https://github.com/ami3go/itech_driver/issues/162) | Source mode aliases | VERIFIED AND MERGED | #196 | Issue closed; see continuation evidence |
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
| [#183](https://github.com/ami3go/itech_driver/issues/183) | Logging import | PARTIALLY IMPLEMENTED | #191 | #191: import defect corrected; static/module sweep pending #185 |
| [#184](https://github.com/ami3go/itech_driver/issues/184) | Logging resources | VERIFIED AND MERGED | #191 | Issue closed; see continuation evidence |
| [#185](https://github.com/ami3go/itech_driver/issues/185) | Static analysis/wheel CI | PARTIALLY IMPLEMENTED | #136 #149 #190 | Static analysis and integrated wheel gate |

## Before/after

Before: fragmented PRs, 4 integrated failures, mandatory VISA dependency on old master. After: single passing integrated master, optional transport extras verified with minimal wheel and native TCP CI, registry inventory aligned, remote preflight/fault behavior regression-tested. Model descriptors, centralized validation, canonical registry semantics, session ownership, lifecycle coverage, static checks and legacy cleanup still require acceptance review and additional implementation.

## Release readiness

Software baseline: PASS for documented offline regression and wheel matrix. Full campaign: NOT COMPLETE. Hardware release qualification: NOT VERIFIED. No physical authorization or measurements. Remaining software issue status must be updated after individual evidence review; no claim of full programming-guide compliance or full release readiness.

## Configuration update

PR #193 merged at a16b25c946acd3bece1ed10fc1a71e45f612710b after reconciled head f24e112de57049e7dbb86d6daa70e0d5dced2a37 passed [offline CI](https://github.com/ami3go/itech_driver/actions/runs/45377662064), [clean wheel](https://github.com/ami3go/itech_driver/actions/runs/45377662096) and native TCP without VISA (run 45377662210). #153 and #154 verified and closed; #150 partial (effective-limit intersection remains). #191 previously passed integrated offline and minimal wheel runs 45377644599/45377644827; reconciled again with #193 at d49ebd1c09c2a0426673763ff32f00541648631b; current CI 45378132484/45378132554 pending at time of recording.

## Continuation evidence — 2026-11-24

Current master at this recording: `e80803358319bf98c0a04669e135f47f93a46295`.
Current shared-core pin: `726c0b01b81c1dd1828e49cc8e531f58910538f5` (merged core #15; [quality matrix](https://github.com/ami3go/scpi-driver-core/actions/runs/45381166551), [N6700 compatibility](https://github.com/ami3go/scpi-driver-core/actions/runs/45381166507), green).

| PR | Tested head | Merged commit | Offline matrix | Clean wheel |
|---|---|---|---|---|
| #191 | d49ebd1c09c2a0426673763ff32f00541648631b | 4668c44ef079e012c5e17ac09c2a2d7a5b6e8fae | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45378132484) | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45378132554) |
| #195 | 695162ff54c72b8915d56cf8c49582d7526e3109 | 1f4100fd528e85b1a6385456efb7bd9da20d23c0 | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45381020665) | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45381020530) |
| #196 | 9c8fa77920236528aa8610baea8cb31c949573b7 | ecd4748f336026c1edee3478bc52a6ade2a67dbb | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45381385792) | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45381385823) |
| #197 | 33e6ee867ffe8cb8bad9dd3d61f77ae310b3e737 | e1f0b876bbb37410570a424059fe0064ee50052f | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45381892970) | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45381892966) |
| #198 | e47419e096ad4f8235d73d4c62faaecd38cd3672 | 4115f3977d625cc9c2a9c12302b8e75806b74394 | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45381951970) | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45381951696) |
| #199 | 764174ae177244341f54bd11058ef4ddcef92fc1 | e80803358319bf98c0a04669e135f47f93a46295 | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45382066743) | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45382066595) |

Closed 15 of 40: #150, #153, #154, #155, #159, #162, #166, #169, #170, #172, #184, #186, #187, #188, #189. These are individually verified software acceptances, not physical qualification. All other issues remain open.

Architecture now has one immutable 26-model rating descriptor map, explicit feature states, separate reported live and effective ranges, application limits, and a single command-to-electrical-rating mapping for five programmed electrical setters. Unknown models cannot authorize these setting writes. Source setpoint bounds use cached generation-scoped core identity, fresh live range, nominal hardware and optional application bounds under the session lock. Protection trip thresholds have separate semantics and are not assigned nominal ratings. The core cache no longer returns stale identity after failed refresh/disconnect. Automatic detection transfers the live session without reopen and cannot discard explicit vendor policy on unknown fallback. No new wire command syntax was introduced in this continuation. Full programming-guide revision/firmware and physical qualification still pending. All new verification was GitHub offline CI, no local full clone or HIL.

Next: #171/#173 per-command capability and qualification guards; #151/#152 centralized validation and command-specific protection ranges; #167 exact ARB integers. #183 global import/static check remains tied to #185. Do not claim release ready.


## Continuation 2 — 2026-11-24 (supersedes earlier status snapshots)

Verified source master: `fda9cbc35f725a2f765031399997f15d0ae1bd40`; core pin unchanged `726c0b01b81c1dd1828e49cc8e531f58910538f5`. Documentation PR #194 already merged. All eight source PRs below merged after exact-head CI and base reconciliation. 25 of 40 campaign issues individually verified and closed, 15 open: #152, #156, #157, #158, #161, #163, #164, #165, #167, #168, #173, #175, #176, #179, #182.

| PR | Tested head | Merge commit | Offline CI | Wheel CI | Acceptance |
|---|---|---|---|---|---|
| #200 | 536745d669f88ee5cd8648fa35e2ce1e6139c14c | 9e17957dbf51b4c4deed4ffd90458a4af1e7dd1a | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45383625936) | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45383625793) | #151 |
| #202 | c156adf9d6ff4d456ae00dd0114311b8e0ab2124 | f1417b57bb4b257dcd25b1c4248d3cc93ddf3378 | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45384375828) | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45384375734) | #171 |
| #201 | 2c8ffb18e501bb000f3ea1b5dae872666fe00476 | 6d5dd520e4db5f36b465f3125694bfd0cdb601fd | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45384405992) | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45384405934) | #177 |
| #203 | 2da3898918e3931a46db3ee23e5f1724ff6afa7d | ed1cb07faaf126078a070171648e6fcf36be4685 | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45384573774) | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45384573673) | #183 #185 |
| #204 | 0b5e45511a75d33418ce30b63aca372ac25d44ef | 0ee0cca0783e4f532284812e2b17ece83c396479 | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45384967100) | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45384967165) | #178 |
| #205 | 24b093be15f729aca4fe02fb3ee5a56a4090d193 | ea83f0bb0f5e955146e2773a09e5f3cbc1fe01fe | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45385087908) | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45385087935) | #167 partial |
| #206 | aaa5f0a997a558adbfa979b20e405a1496afcf6e | 9bd84b81184db9d3b688eb596c1c87c2013c0892 | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45385652073) | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45385652194) | #174 |
| #207 | c8867e6d539dc1ccbc16c417447952b9d3c6dd9a | fda9cbc35f725a2f765031399997f15d0ae1bd40 | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45385686520) | [4/4](https://github.com/ami3go/itech_driver/actions/runs/45385686524) | #160 #180 #181 |

Latest source CI Linux Python 3.13: 709 passed, 2 deselected, 8 warnings; sdist and wheel built. [Static/public-import checks 8/8](https://github.com/ami3go/itech_driver/actions/runs/45385686485) (Linux/Windows Python 3.10–3.13), [native TCP without VISA](https://github.com/ami3go/itech_driver/actions/runs/45385686514) green. Static scope: Ruff undefined-name checks and scoped mypy, not blanket full-project typing. Clean wheels exercise missing backend diagnostics, optional extras, simulator and CLI. Shared VISA manager ownership tested with PyVISA-sim. No physical access; no independent local full-clone run.

Changes: explicit shared numeric and channel validation; four-state capability evidence without speculative probes; bounded explicit identity-only retry through core; supervised CLI activation with explicit limits, readback, residual checks and same-generation shutdown; watchdog sequence lock and final state verification; primary-error preservation and metadata-only release version with 0+unknown source fallback. ARB exact integer checks merged, but #167 remains open: family LIST envelope from user manual V2.6/5 (May 2025) pp. 58–59 is not proof of every model/firmware command bound; zero repeat excluded by finite-only policy. #152 protection limits require separate verified command-specific semantics, not nominal ratings or speculative MIN/MAX queries. #173 per-command feature enforcement remains open. Do not claim full programming-guide or HIL qualification or release readiness.
