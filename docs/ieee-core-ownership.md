# Shared IEEE ownership

All legacy IEEE488 methods delegate to session.ieee488 via the driver policy
adapter. Raw IDN and OPC responses retain their existing string contract;
self-test retains integer return. Reset and recall revoke remote authorization.
The explicit *STB? API is not transport serial poll; *ESR? stays destructive
and never replayed. Standard event enable/status registers use 8-bit validation
in the core. Model-specific save/recall maximum slots are not inferred;
integer/negative checks do not establish hardware qualification. The updated
core pin passed its quality matrix and N6700 compatibility before integration.
