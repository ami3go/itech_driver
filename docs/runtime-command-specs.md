# Runtime command specifications (increment 1)
The immutable runtime registry owns wire headers and typed result/argument
metadata for measurement/fetch (scalar and array) and output state methods.
Scalar operations share one executor and core parsers. Arrays retain explicit
format qualification through the existing helpers, consuming registry headers.
The simulator shares registry headers for measured quantities and output state.
Legacy wire syntax and remote guards are preserved; no physical support is
inferred. The historical inventory remains separately checked for complete
public method coverage. Remaining methods, compound operations, capability
policy and authoritative guide references must be migrated before #168 closes.


## Increment 2
48 additional direct scalar reads and literal writes migrate to typed specs, preserving their surrounding validation. IEEE operations already owned by the core remain delegated there. Explicit destructive-read effect metadata is recorded for error/event reads; no operation may be automatically replayed. Compound/parameterized methods still need migration. All guide states remain unverified unless independently evidenced.
