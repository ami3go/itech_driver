# Master runbook — communication increment only

## Offline gate

From a checkout in a dedicated environment on Windows or Linux:

    python -m pip install -e ".[dev,discovery]"
    python -m pytest
    python scripts/hil/run_hil.py --list
    python scripts/hil/run_hil.py --dry-run --suite full

No authorization or physical connection for these commands. Default CI excludes
hardware. Never use real endpoints with offline simulators.

## Operator preparation

Obtain manufacturer programming guide (part 402225, copyright 2024, candidate
V1.4/09,2024 per existing repository) and exact user manual from the ITECH
IT-M3900D product download page. Distributor PDF:
https://www.altoo.dk/files/itech/manuals/IT-M3900D-Programming-Guide.pdf
Official product page:
https://www.itechate.com/en/product/dc-power-supply/IT-M3900D.html
Revision, PDF hash, page images and firmware applicability must be independently
verified before guide closure. The candidate page images were not retrievable
during this increment.

A qualified operator verifies model-specific AC installation and protective
earth, ratings, connector and cable suitability, ventilation and environmental
conditions using the actual manual. Use the approved bench procedure for isolation,
independent voltage/current verification, accessible emergency disconnect and
attendance. For communication-only tests disconnect DUT and external DC sources,
leave the DC terminals safely isolated, confirm output off on panel and independently
verify de-energization. Do not touch exposed DC terminals. Do not energize.

Topology: host -> one approved communication interface -> ITECH;
DC terminals isolated from DUT and all external energy sources.
Independent rated measuring equipment verifies safe state via approved connections.
AC supply/protective earth remain as prescribed by the model installation manual.

Copy configs/hil/bench.example.json to an external operator-owned file. Populate
every field from the actual configuration, including unused transport fields
(they are not sent to hardware on other interfaces); do not guess values.
Record exact serial/model/firmware from the panel, independent safe-state
reference and emergency procedure reference. All booleans are operator attestations,
not measured interlocks. For remote/local, explicitly set remote_local true
only if the panel can be observed and no DC energy is connected.
For all energized work this increment intentionally refuses execution.

## Authorization

In a private directory outside the checkout, create the local authority once:

    python scripts/hil/generate_hil_key.py --enroll --authority /private/authority.json

Issue one scope-bound key (replace paths with actual external paths):

    python scripts/hil/generate_hil_key.py --authority /private/authority.json --config /private/bench.json --key /private/permit.json

The operator enters the PIN interactively; never send it to an agent or log.
Use a new permit filename for renewal. Files are created exclusively; on POSIX
mode 0600. On Windows enforce equivalent NTFS ACLs on the private directory.
Authority contains a signing secret: never commit or share it. Restrict access
and protect operator control; a process with authority-file read/write access
can forge a permit, so this is a cooperative execution guard, not isolation
against a malicious local process. The PIN verifier is salted PBKDF2; permit
is HMAC-bound to the entire configuration and valid for at most 24 hours.
Changing a configuration field invalidates the permit. Never store permits or
authority in evidence. Delete/revoke local authority if compromised; existing
permits cannot be used with a newly enrolled authority.

## Local preflight and physical tests

    python scripts/hil/run_hil.py --preflight --config /private/bench.json --authority /private/authority.json --key /private/permit.json
    python scripts/hil/run_hil.py --suite HIL-COM-ID --config /private/bench.json --authority /private/authority.json --key /private/permit.json --evidence /private/evidence-id
    python scripts/hil/run_hil.py --suite HIL-COM-REMOTE --config /private/bench.json --authority /private/authority.json --key /private/permit.json --evidence /private/evidence-remote

Windows: substitute absolute paths under an ACL-protected directory. Select
tcp, visa-lan, usbtmc or vcp only when documented and actually installed.
Repeat with a separate configuration and permit for each exact interface
and OS. Local preflight checks permit and configuration only, not equipment.
The existing pytest hardware entry point checks the permit at collection
and before each hardware test; it also checks actual exact identity before
remote/local operation. Tests do not energize output. No automatic reconnect,
reset, protection clear or ON. Do not use raw driver access as a permit bypass.

HIL-COM-ID (P0): execute first, with isolated DC terminals; compare actual
model/serial/firmware with panel record; repeated IDN must match and session
must close. Preserve JUnit plus operator observation, transport and OS details.
Any mismatch, timeout or failure: STOP; do not change address to discover
other instruments. Recheck wiring, interface settings and approved scope.

HIL-COM-REMOTE (P1): only after ID case passes and remote_local is approved.
Observe panel before/during/after the remote/local test. Expected remote then
local; JUnit only checks requested mode, not actual panel state. Record actual
panel state and exceptions independently. A missing panel record is INCONCLUSIVE.
If failure or uncertain state, STOP, use approved physical isolation procedure.

After each test: independently verify output remains safe, record evidence,
and release interface. If communication is lost, software output state is
UNKNOWN: stop, use independent emergency path, isolate energy and verify
safe state with approved equipment. Driver close is not output disable.
No further physical tests until operator re-establishes preconditions.

## Evidence and release

Use existing docs/qualification_manifest.template.json and
docs/physical_evidence_template.json to freeze case inventory before testing.
Run existing offline structural checker:
    python -m itech_driver.qualification evidence.json --artifacts evidence_directory --manifest approved_manifest.json

Preserve original logs/JUnit and raw independent measurements separately from
simulation. Required rows must be passed with hashed evidence and independent
technical approval; the structural checker cannot establish authenticity.
Existing schema uses PASS, FAIL, NOT_RUN, UNKNOWN; map NOT RUN to NOT_RUN,
INCONCLUSIVE to UNKNOWN only for export. BLOCKED/NOT IMPLEMENTED must remain
unpassed; exclusions need independent approval. No synthetic physical evidence.

## Stop / continue

Invalid permit, identity mismatch, unsafe/unknown state, missing guide evidence
for a proposed command, communication failure, expired permit or missing
equipment: STOP physical sequence. Preserve evidence and obtain independent
safe-state verification. No automatic resume. Offline analysis can continue.
A new approved scope and fresh preflight are required after any interruption.

## Remaining work

See test_matrix.json: blocked cases are work packages, not executable HIL test
cases. No physical source/sink/protection/ARB/trigger/measurement/recovery/
performance/soak execution is implemented here. Model capability descriptors
are nominal, not firmware-qualified. The 300 registry rows do not establish
the number of unique SCPI commands or full public API coverage. All mandatory
P0 and P1 qualification must pass per model/firmware/interface before release.
No hardware qualification is claimed.