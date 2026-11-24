# ITECH-COM-02 — USB virtual COM
Dependency: COM-01 (optional transport packaging).
## Requirements
- Use core SerialTransport and optional pyserial; no VISA required.
- Explicit COM port or Linux device path; defaults 9600/8/N/1 as user manual p.12, §2.5.1 p.27; match front panel configuration.
- Configurable baud, data bits, parity, stop bits, LF or CRLF terminator, finite read/write timeouts; no automatic scanning or remote mode.
- Reject invalid settings before opening. Preserve raw VISA resource API.
## Acceptance
Fake pyserial backend exercises public driver → real core serial path, exact transmitted bytes, settings and close. Test invalid settings and real pyserial loopback framing. Physical qualification COM-05; do not open a physical port in CI.
