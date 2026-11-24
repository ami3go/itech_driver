# ITECH-COM-03 — USB and LAN discovery
Dependency: COM-01 and COM-02.
## Requirements
- Enumerate USBTMC and TCPIP VISA resources; optionally discover LXI/VXI-11 and SCPI raw service advertisements using mDNS. Enumerate USB VCP candidates by serial-port USB metadata but probe VCP only when explicitly enabled with matching settings.
- Explicit subnet fallback limited to IPv4 private/link-local network of at most 256 addresses; no implicit subnet scan; one configured SCPI socket port, bounded workers and per-probe timeout. No reset, remote, output, or other write.
- Only valid manufacturer/model identities qualify as ITECH IT-M3900D family, including actual variant model strings (IT-M3902D-80-40 etc.). Group duplicate serials with all endpoint addresses retained; do not collapse missing serials.
- Return endpoint, interface, identity and per-endpoint diagnostic information. Close every probe session. Missing optional discovery backend is a diagnostic, not a global failure.
- CLI discover supports explicit subnet, port, timeout and opt-in VCP.
## Acceptance
Mock enumeration and probes (no LAN or USB access in CI), duplicates, non-ITECH/malformed responses, timeouts, bad subnet, missing backends, model variants. Explicit operator invocation only for real discovery; physical qualification COM-05.
