# Qualification work inventory

- **HIL-COM-ID (P0)** — Repeated IDN and exact model/serial/firmware; session cleanup. Existing physical test; operator final independent check. Status: NOT RUN.
- **HIL-COM-REMOTE (P1)** — Remote/local command sequence; panel observation mandatory; no energized output. Status: NOT RUN.
- **HIL-COM-DISC (P0)** — Scoped physical discovery, framing, partial response, timeout, interface parity and reconnect; per OS/interface. Status: BLOCKED.
- **HIL-SRC (P0)** — All supported source controls, setpoint validation, independent output behavior and boundaries. Status: BLOCKED.
- **HIL-SINK (P0)** — Only if exact model guide establishes sink and regeneration; no assumptions from other families. Status: BLOCKED.
- **HIL-PROT (P0)** — Configuration separate from bounded trip/reset; verify no automatic output enable. Status: BLOCKED.
- **HIL-ARB (P1)** — Physical waveform, points, count, timing, trigger, abort; exact integer bounds. Status: BLOCKED.
- **HIL-TRIG (P1)** — All implemented trigger paths; external timing reference. Status: BLOCKED.
- **HIL-MEAS (P1)** — Calibrated independent reference, uncertainty and guide limits. Status: BLOCKED.
- **HIL-REC (P0)** — Transport failures, unknown output, operator emergency isolation, no replay. Status: BLOCKED.
- **HIL-PG (P0)** — Per-command guide traceability and independent approval. Status: BLOCKED.
- **HIL-CORE (P0)** — Pinned core contract, transport cleanup, replay policy. Status: BLOCKED.
- **HIL-PERF (P1)** — Compare interfaces, host and physical latency separately. Status: BLOCKED.
- **HIL-SOAK15 (P1)** — 15-minute smoke profile. Status: BLOCKED.
- **HIL-SOAK1 (P1)** — 1-hour short profile. Status: BLOCKED.
- **HIL-SOAK4 (P1)** — 4-hour extended profile. Status: BLOCKED.
- **HIL-SOAK24 (P1)** — 24-hour standard profile; renew authorization before expiration at safe checkpoint. Status: BLOCKED.
- **HIL-SOAK72 (P2)** — 72-hour extended reliability; renewal at safe checkpoints. Status: BLOCKED.
- **HIL-MODEL (P0)** — Exact model/firmware/interface and capability guards. Status: BLOCKED.

Only the two communication cases are implemented. The remaining entries are blockers, not test procedures or release coverage.
