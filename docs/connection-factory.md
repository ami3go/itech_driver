# Unified connection factory
Legacy VISA resource strings remain supported. Explicit tcp://host:port and
vcp:PORT resources select core TCP/serial without optional VISA imports.
ConnectionConfig is immutable and creates an unopened ScpiSession; drivers
open and own it once. connect_tcp and connect_vcp delegate to this factory.
Independent command_termination/response_termination override the legacy
termination alias (LF, CRLF or CR). No endpoint is guessed from a bare host.
An explicit ConnectionConfig cannot be mixed with legacy overrides or
injected transport. No hardware qualification is implied.
