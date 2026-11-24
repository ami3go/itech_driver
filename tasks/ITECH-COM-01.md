# ITECH-COM-01 — Native TCP without VISA
## Requirements
- Use pinned core TcpTransport; no PyVISA import or dependency for native TCP.
- Default TCP port 30000 and LF framing per IT-M3900D user manual quick reference pp. 12–13 and §2.5.2.3 p.31. Allow explicit port and finite timeout in milliseconds.
- Explicit host/port only, no network scan, no constructor SCPI or output changes, no automatic replay. Preserve legacy VISA API via optional extra.
- Public connect_tcp(host, port=30000, timeout=5000) returns ITM3900D, same subsystems.
## Acceptance
Local loopback server verifies exact LF command and fragmented response, close and bounded failure; no VISA installed in dedicated native CI job. No real hardware in CI. Hardware socket qualification belongs to COM-05.
Source: https://www.itechate.com/uploadfiles/%E7%94%A8%E6%88%B7%E6%89%8B%E5%86%8C/user%20manual/it-m3900d/IT-M3900D%20User%20Manual-EN.pdf
