# ITECH-COM-04 — Explicit remote mode
Dependency: COM-03.
## Requirements
- User manual §2.5 p.27 requires SYST:REM before settings changes; programming guide p.16 defines SYST:REM and SYST:LOC, no response.
- Public enter_remote(), return_local(), remote_mode() context manager; system.remote/local route to same implementation. No hidden remote commands on construction, discovery, or close.
- Record only last successfully requested mode in current core session generation, not verified physical mode. Invalidate on disconnect, reopen, reset/preset or failed I/O.
- Optional require_remote=True blocks public write_scpi/subsystem writes before request. Raw client escape hatch and query side effects are not covered; not a safety interlock. Keep default false for compatibility. CLI explicitly enters remote for setting changes and returns local afterward.
- Never retry or silently re-enter remote after failures. Context preserves primary exception when cleanup fails.
## Acceptance
Scripted exact REM/LOC ordering, read-only access, blocked write, failed entry, reconnect invalidation, context cleanup, no implicit close command. Physical panel behavior verified separately.
Source: https://www.altoo.dk/files/itech/manuals/IT-M3900D-Programming-Guide.pdf
