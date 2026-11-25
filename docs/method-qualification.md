# Explicit subsystem method qualification (increment 1)

Use require_qualified_capabilities=True to require explicit exact model,
firmware and core transport kind evidence for each attached typed subsystem
operation. bind_method_qualification(profile) refreshes identity once,
binds to the session generation and enables strict mode even if binding fails.
Unknown, unsupported or unqualified methods are rejected without command I/O.
A reconnect or changed identity invalidates the binding. Logging instance
keys distinguish ELOG and DLOG. Compound methods may require evidence for
each nested typed operation. Common identity remains available.

The evidence reference is an external caller attestation, not manufacturer
certification or HIL authorization. No built-in firmware support matrix is
asserted. Legacy constructors retain permissive behavior for compatibility;
strict mode is opt-in. Raw SCPI/client/session are explicit low-level paths outside the typed guards.
Directly instantiated subsystems are covered by class-level enforcement below.
Compound lifecycle helpers perform the preflight documented below. Existing remote mode and parameter
validation still apply. This is not a hardware safety boundary or complete
#173 acceptance.


## Compound operations
Acquisition and ARB arm preflight all nested required capabilities before the first configuration write. Supervised ON checks the full observation/protection/setpoint/enable capability list before any query or write. OFF is allowed with qualified state-set capability even if observation is not qualified; the result is UNKNOWN, never a safe-state assertion. Registry scalar execution cannot bypass the typed guard. Other compound operations and direct raw/client access still need separate review. No HIL authorization is implied.

## Class-level enforcement
Guard installation now occurs on subsystem classes rather than attached instances. Directly constructed subsystem objects with an ITM3900D parent therefore use the same qualification lock and method evidence. Explicitly unsupported battery execution, acquisition readback, generic trigger functions and DLOG raw-data methods cannot be promoted by a caller profile. The legacy compatibility default remains unchanged. Raw SCPI and direct core access remain explicit low-level interfaces; no firmware support is inferred.

## Single capability inventory
Method qualification keys and restricted dispositions now derive directly from the immutable runtime command registry rather than a second 300-key list. IEEE identity and the offline planner are excluded; ELOG and DLOG retain separate evidence and DLOG raw data remains restricted. Class installation checks actual methods against the derived set. Legacy opt-in behavior is unchanged; external model/firmware evidence remains necessary.

## Live range reads
All 20 range-validated source setters require matching read-method qualification before identity or MIN/MAX probes. Resistance configuration also preflights the CV-priority query. Explicit capability discovery preflights all five electrical read methods. A qualification reference for these queries must cover the bound selectors when they are used for range discovery; ordinary scalar syntax alone is not evidence of MIN/MAX support. Legacy mode and existing command envelopes remain unchanged.
