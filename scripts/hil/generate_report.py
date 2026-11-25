"""Offline exports of an operator-supplied report and independent manifest.

No output from this utility establishes physical authenticity or release approval.
"""
import argparse
import csv
import html
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from itech_driver.qualification import check_release_evidence

ROOT = Path(__file__).resolve().parents[2]
FIELDS = ("case_id", "model", "serial", "firmware", "interface", "command",
          "guide_page", "expected", "actual", "utc", "result", "required", "energized")
NONPASS = {"BLOCKED": "UNKNOWN", "NOT APPLICABLE": "NOT_RUN",
           "NOT IMPLEMENTED": "NOT_RUN", "INCONCLUSIVE": "UNKNOWN"}


def export(report, manifest, artifacts, output):
    from jsonschema import Draft202012Validator
    schema = json.loads((ROOT / "schemas/hil_evidence.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    if not validator.is_valid(report):
        raise ValueError("evidence schema rejected; no exports created")
    normalized = dict(report, rows=[dict(row, result=NONPASS.get(row["result"], row["result"]))
                                    for row in report["rows"]])
    errors = check_release_evidence(normalized, manifest, artifacts)
    evidence_type = report["evidence_type"]
    verdict = "NOT QUALIFIED" if evidence_type == "physical" else "NOT EXECUTED"
    status = "STRUCTURE PASSED" if not errors else "STRUCTURE FAILED"
    # Keep manifest and raw data separately. Deliberately omit authorization
    # secrets, raw command traces and free-form checker errors from exports.
    rows = [{k: row[k] for k in FIELDS} for row in report["rows"]]
    summary = {"evidence_type": evidence_type, "structural_status": status,
               "physical_verdict": verdict, "technical_review_required": True,
               "structural_error_count": len(errors),
               "driver_commit": report["driver_commit"], "core_commit": report["core_commit"],
               "guide_revision": report["guide_revision"], "guide_sha256": report["guide_sha256"],
               "rows": rows}
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / "report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (output / "report.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("evidence_type", "structural_status", *FIELDS))
        writer.writeheader()
        for row in rows:
            # Prevent spreadsheet formula interpretation of operator-entered fields.
            cells = {k: ("'" + v if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@")) else v)
                     for k, v in row.items()}
            writer.writerow(dict(cells, evidence_type=evidence_type, structural_status=status))
    header = f"{evidence_type.upper()} evidence — {status}; physical verdict: {verdict}"
    def md(value):
        return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")
    table = ["| Case | Model | Interface | Reported result |", "|---|---|---|---|"]
    table.extend("| " + " | ".join(md(row[k]) for k in ("case_id", "model", "interface", "result")) + " |" for row in rows)
    (output / "report.md").write_text("# " + header + "\n\nIndependent technical review required.\n\n" +
                                      "\n".join(table) + "\n", encoding="utf-8")
    hrows = "".join("<tr>" + "".join("<td>" + html.escape(str(row[k])) + "</td>" for k in FIELDS)
                    + "</tr>" for row in rows)
    (output / "report.html").write_text("<!doctype html><meta charset='utf-8'><title>ITECH qualification</title><h1>" +
        html.escape(header) + "</h1><p>Independent technical review required.</p><table><thead><tr>" +
        "".join("<th>" + k + "</th>" for k in FIELDS) + "</tr></thead><tbody>" + hrows + "</tbody></table>",
        encoding="utf-8")
    suite = ET.Element("testsuite", name="ITECH-" + evidence_type + "-reported-evidence",
                       tests=str(len(rows)+1))
    properties = ET.SubElement(suite, "properties")
    for name, value in (("evidence_type", evidence_type), ("physical_verdict", verdict),
                        ("structural_status", status), ("technical_review_required", "true")):
        ET.SubElement(properties, "property", name=name, value=value)
    failures = skipped = 0
    for row in rows:
        tc = ET.SubElement(suite, "testcase", name=row["case_id"])
        if row["result"] == "FAIL":
            ET.SubElement(tc, "failure", message="Operator-reported failure")
            failures += 1
        elif row["result"] != "PASS":
            ET.SubElement(tc, "skipped", message=row["result"])
            skipped += 1
        # PASS in input is only a reported result; mark as not independently
        # qualified in JUnit even when structurally valid.
        else:
            ET.SubElement(tc, "skipped", message="Reported PASS; technical review required")
            skipped += 1
    gate = ET.SubElement(suite, "testcase", name="manifest-structure")
    if errors:
        ET.SubElement(gate, "failure", message="Structural evidence gate failed")
        failures += 1
    suite.set("failures", str(failures))
    suite.set("skipped", str(skipped))
    ET.ElementTree(suite).write(output / "report.xml", encoding="utf-8", xml_declaration=True)
    return bool(errors)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("report")
    p.add_argument("--manifest", required=True)
    p.add_argument("--artifacts", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    try:
        return int(export(json.loads(Path(a.report).read_text(encoding="utf-8")),
                          json.loads(Path(a.manifest).read_text(encoding="utf-8")),
                          a.artifacts, a.output))
    except (OSError, ValueError):
        p.exit(2, "Evidence export rejected; check schema and paths.\n")


if __name__ == "__main__":
    raise SystemExit(main())
