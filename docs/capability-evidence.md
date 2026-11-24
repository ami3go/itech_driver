# Capability evidence contract

Generic capability discovery is an offline metadata operation. The legacy
None result is preserved, while capability_states() distinguishes unknown,
unsupported, supported and unqualified. Unknown is not proof of absence.
ModelDescriptor requires explicit evidence, not a successful response to an
arbitrary probe. Existing nominal model ratings do not qualify firmware or
optional features. The separate explicit identity/range operations propagate
communication and parse failures. No error queue is drained to establish
capability. Synthetic unsupported-state tests are not evidence of absence of
a real hardware option. Subsystem-wide runtime qualification remains #173.
