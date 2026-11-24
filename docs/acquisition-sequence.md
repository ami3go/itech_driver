# Compound acquisition setup
Use AcquisitionConfig and configure_and_arm for one serialized host-side
configuration sequence: points, offset, interval, trigger source, initiate.
All local arguments are validated before the first command; failed writes
stop the sequence without trigger, reconnect or replay. Immediate source is
excluded from this compound API. Existing low-level setters and acquire_start
remain available. Success means transmission, not instrument-ready readback.
The sequence is bounded to five finite-timeout core transactions; lock
contention is outside that budget. Model-specific acquisition limits and
readback remain unqualified and are not invented. Caller must independently
verify acquisition readiness before explicit software trigger.
