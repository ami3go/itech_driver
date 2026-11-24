from hashlib import sha256
from copy import deepcopy
from itech_driver.qualification import check_release_evidence


def fixture(root):
    trace=root/"trace.txt"
    trace.write_text("synthetic test evidence")
    meta=dict(driver_commit="a"*40,core_commit="b"*40,guide_revision="synthetic",
              guide_sha256="c"*64)
    case=dict(case_id="VOLT-001",model="M",serial="S",firmware="F",interface="TCP",
              command="MEAS:VOLT?",guide_page="200",expected="0",energized=False)
    other=dict(case,case_id="VOLT-002",expected="1")
    manifest=dict(meta,approval_reference="synthetic",cases=[case,other])
    rows=[dict(x,actual=x["expected"],utc="synthetic",result="PASS",required=True,
               artifacts=[dict(path=trace.name,sha256=sha256(trace.read_bytes()).hexdigest())])
          for x in manifest["cases"]]
    report=dict(meta,authorization_reference="synthetic",rows=rows)
    return report,manifest


def test_manifest_allows_distinct_cases_same_command(tmp_path):
    report,manifest=fixture(tmp_path)
    assert check_release_evidence(report,manifest,tmp_path)==[]


def test_omitted_case_rejected(tmp_path):
    report,manifest=fixture(tmp_path)
    report["rows"].pop()
    assert any("missing required manifest case" in e for e in check_release_evidence(report,manifest,tmp_path))


def test_downgraded_case_and_wrong_commit_rejected(tmp_path):
    report,manifest=fixture(tmp_path)
    report["driver_commit"]="d"*40
    report["rows"][0]["required"]=False
    errors=check_release_evidence(report,manifest,tmp_path)
    assert any("binding mismatch" in e for e in errors)
    assert any("not passed" in e for e in errors)


def test_energized_flag_cannot_be_omitted_or_safe_state_unhashed(tmp_path):
    report,manifest=fixture(tmp_path)
    report["rows"][0].pop("energized")
    assert check_release_evidence(report,manifest,tmp_path)
    report,manifest=fixture(tmp_path)
    manifest["cases"][0]["energized"]=True
    report["rows"][0]["energized"]=True
    report["rows"][0]["independent_safe_state_reference"]="unverified.txt"
    assert any("not a hashed artifact" in e for e in check_release_evidence(report,manifest,tmp_path))


def test_expected_result_cannot_be_rewritten(tmp_path):
    report,manifest=fixture(tmp_path)
    report["rows"][0]["expected"]="999"
    assert any("case mismatch" in e for e in check_release_evidence(report,manifest,tmp_path))
