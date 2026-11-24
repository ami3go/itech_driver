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

## Increment 3
140 additional methods use registered fixed headers for parameterized operations, scalar reads or validated subsystem helpers. The parameterized executor rejects multiple program messages. Existing typed validation and response handling are retained. Metadata identifies validated formatted payloads; field-level typed templates and remaining dynamic/compound operations are not yet fully migrated. Guide qualification remains separate.
