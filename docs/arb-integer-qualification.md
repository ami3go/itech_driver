# ARB integer qualification
Explicit ArbIntegerQualification binds per-command positive integer bounds
to exact model/firmware and live session generation. Bounds are externally
attested, not verified by the driver; the family envelope remains a conservative
upper ceiling, not a claim of device capability. Strict method qualification
requires these bounds in addition to method evidence. In legacy mode, existing
family-only behavior remains unless an explicit integer profile is bound.
Failed binding or reconnect prevents further qualified integer operations
until a successful bind. No speculative MIN/MAX probes or unverified
termination commands. ARB lifecycle checks the count before configuring trigger
source. Command-specific manufacturer range evidence remains outstanding.
