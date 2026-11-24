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
