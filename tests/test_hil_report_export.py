"""Synthetic fixtures only; no physical evidence or hardware I/O."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts/hil" / (name+".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_artifact_and_report_export(tmp_path):
    collect = load("collect_evidence").collect
    export = load("generate_report").export
    (tmp_path / "trace.txt").write_text("synthetic")
    artifacts = collect(tmp_path, ["trace.txt"])
    with pytest.raises(ValueError):
        collect(tmp_path, ["../outside"])
    meta = dict(driver_commit="a"*40, core_commit="b"*40, guide_revision="synthetic",
                guide_sha256="c"*64)
    case = dict(case_id="synthetic", model="synthetic", serial="synthetic", firmware="synthetic",
                interface="mock", command="fixture", guide_page="synthetic", expected="0",
                energized=False)
    manifest = dict(meta, approval_reference="synthetic", cases=[case])
    row = dict(case, actual="0", utc="synthetic", result="PASS", required=True, artifacts=artifacts)
    report = dict(meta, evidence_type="simulated", authorization_reference="not required", rows=[row])
    output = tmp_path / "export"
    assert export(report, manifest, tmp_path, output) is False
    assert {p.name for p in output.iterdir()} == {"report.json", "report.csv", "report.md", "report.html", "report.xml"}
    saved = json.loads((output / "report.json").read_text())
    assert saved["physical_verdict"] == "NOT EXECUTED"
    assert saved["technical_review_required"] is True
    row["result"] = "BLOCKED"
    assert export(report, manifest, tmp_path, tmp_path / "blocked")
    row["result"] = "PASS"
    (tmp_path / "trace.txt").write_text("tampered")
    assert export(report, manifest, tmp_path, tmp_path / "tampered")
    report.pop("evidence_type")
    with pytest.raises(ValueError):
        export(report, manifest, tmp_path, tmp_path / "bad")
