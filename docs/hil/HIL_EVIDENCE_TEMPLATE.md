# Evidence collection and reporting

Reuse docs/qualification_manifest.template.json and
docs/physical_evidence_template.json. Add evidence_type = "physical" or
"simulated" to the report; no simulation result can establish physical PASS.
Before test, independently approve case IDs, expected results and model,
firmware, interface, guide revision and hashes. Preserve all failures.
Keep raw traces, independent reference readings, calibration and safe-state
records in a new evidence directory. Never place credentials, private signing
keys or permits in evidence. Explicitly review trace files for secrets before
collecting. The scripts do not scan raw binaries for credentials.

After capturing files, generate hashes (example paths are actual captured files,
not placeholders to create synthetic physical evidence):

    python scripts/hil/collect_evidence.py --root evidence --output evidence/artifacts.json trace.txt results.xml

Attach relevant digest rows to the corresponding case in the evidence JSON.
For energized tests attach the independent safe-state file and reference its
path. Record actual result, UTC, required flag and reported status. BLOCKED,
NOT APPLICABLE, NOT IMPLEMENTED and INCONCLUSIVE map to unpassed legacy states
for the structural gate, not to PASS. Do not use NOT APPLICABLE to downgrade a
mandatory requirement. Approved exclusions belong in the independent manifest
review.

    python scripts/hil/generate_report.py evidence.json --manifest approved_manifest.json --artifacts evidence --output evidence-export

The new output directory contains JSON, CSV, Markdown, HTML and JUnit XML.
The export applies JSON Schema and the existing manifest checker; nonzero
exit means evidence invalid or incomplete. It never emits a physical qualified
verdict. JUnit distinguishes reported PASS from independent approval. Preserve
original execution JUnit separately. The existing qualification checker still
requires independent technical review and complete manifest scope.
This increment does not yet automate physical trace, independent measurement,
waveform or environment capture; do not claim the evidence framework complete.
