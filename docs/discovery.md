# Discovery
Install `.[discovery]` to enable VISA enumeration, mDNS and VCP metadata.
```sh
itech-discover
itech-discover --subnet 192.168.0.0/24 --port 30000 --timeout 500
itech-discover --vcp --baudrate 9600
```
The default enumerates advertised USBTMC/LAN VISA resources and IPv4 mDNS
VXI-11/raw-SCPI advertisements. It does not scan arbitrary subnets. VISA
discovery completeness and enumeration time are backend dependent; mDNS
advertisements are not guaranteed on every firmware or network. Explicit
private subnet fallback scans a single SCPI port with bounded workers and
per-probe timeout, only when requested. VCP probes are opt-in and use default
8N1; use connect_vcp for other serial settings. Only IDN is sent; no remote
mode or setting changes. Discovery must be invoked by an authorized operator
on the bench network, not by default CI.
