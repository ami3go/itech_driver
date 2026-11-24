from hashlib import sha256
from itech_driver.qualification import check_evidence


def report(tmp_path):
    p=tmp_path/"trace.txt"
    p.write_text("synthetic test artifact")
    return dict(driver_commit="test",core_commit="test",guide_revision="test",guide_sha256="test",
        authorization_reference="synthetic",rows=[dict(model="test",serial="test",firmware="test",
        interface="test",command="TEST?",guide_page="1",expected="1",actual="1",utc="test",
        result="PASS",required=True,energized=False,artifacts=[dict(path=p.name,sha256=sha256(p.read_bytes()).hexdigest())])])


def test_evidence_gate(tmp_path):
    r=report(tmp_path)
    assert check_evidence(r,tmp_path)==[]
    r["rows"][0]["result"]="NOT_RUN"
    assert check_evidence(r,tmp_path)


def test_tamper_and_missing_safe_state(tmp_path):
    r=report(tmp_path)
    r["rows"][0]["energized"]=True
    (tmp_path/"trace.txt").write_text("changed")
    errors=check_evidence(r,tmp_path)
    assert any("digest" in e for e in errors)
    assert any("safe-state" in e for e in errors)


def test_empty_and_path_escape(tmp_path):
    assert check_evidence({"rows":[]},tmp_path)
    r=report(tmp_path)
    r["rows"][0]["artifacts"][0]["path"]="../other"
    assert check_evidence(r,tmp_path)
