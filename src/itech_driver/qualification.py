"""Offline structural HIL evidence checker. Never contacts hardware."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def check_evidence(report,root):
    errors=[]
    if not isinstance(report,dict):
        return ["report must be an object"]
    for key in ("driver_commit","core_commit","guide_revision","guide_sha256","authorization_reference"):
        if not isinstance(report.get(key),str) or not report[key].strip():
            errors.append("missing "+key)
    rows=report.get("rows")
    if not isinstance(rows,list) or not rows:
        return errors+["no per-command evidence rows"]
    seen=set()
    required=0
    root=Path(root).resolve()
    for i,row in enumerate(rows):
        prefix=f"row {i}: "
        if not isinstance(row,dict):
            errors.append(prefix+"not an object")
            continue
        keys=("model","serial","firmware","interface","command","guide_page","expected","actual","utc","result")
        missing=[k for k in keys if not isinstance(row.get(k),str) or not row[k].strip()]
        if missing:
            errors.append(prefix+"missing "+",".join(missing))
        identity=tuple(str(row.get(k,"")) for k in ("model","serial","firmware","interface","command","case_id"))
        if identity in seen:
            errors.append(prefix+"duplicate command/identity/interface")
        seen.add(identity)
        if type(row.get("required")) is not bool:
            errors.append(prefix+"required flag missing")
        if row.get("result") not in ("PASS","FAIL","NOT_RUN","UNKNOWN"):
            errors.append(prefix+"invalid result")
        if row.get("required") is True:
            required+=1
            if row.get("result")!="PASS":
                errors.append(prefix+"required row not passed")
        if row.get("result")!="PASS":
            continue
        artifacts=row.get("artifacts")
        if not isinstance(artifacts,list) or not artifacts:
            errors.append(prefix+"no artifact evidence")
            continue
        for artifact in artifacts:
            try:
                p=(root/artifact["path"]).resolve()
                if not p.is_relative_to(root) or not p.is_file():
                    raise ValueError("missing or out-of-tree artifact")
                digest=hashlib.sha256(p.read_bytes()).hexdigest()
                if digest!=artifact["sha256"]:
                    raise ValueError("digest mismatch")
            except (OSError,KeyError,TypeError,ValueError) as exc:
                errors.append(prefix+"invalid artifact: "+str(exc))
        if type(row.get("energized")) is not bool:
            errors.append(prefix+"energized flag must be boolean")
        if row.get("energized") is True and not row.get("independent_safe_state_reference"):
            errors.append(prefix+"missing independent safe-state reference")
    if required==0:
        errors.append("no required qualification rows")
    return errors



# Independent inventory, frozen before collection. Each case ID distinguishes
# boundary, failure, setter/readback and repeated cases for one command.
_BINDINGS = ("driver_commit", "core_commit", "guide_revision", "guide_sha256")
_FIELDS = ("model","serial","firmware","interface","command","guide_page","expected","energized")


def check_release_evidence(report, manifest, root):
    """Structural coverage against an independently supplied approved manifest.

    Does not authenticate an operator, prove measurements or approve hardware.
    """
    errors = check_evidence(report, root)
    if not isinstance(manifest, dict) or not isinstance(report, dict):
        return errors + ["manifest and report must be objects"]
    if not isinstance(manifest.get("approval_reference"), str) or not manifest["approval_reference"].strip():
        errors.append("manifest approval reference missing")
    for key in _BINDINGS:
        value = manifest.get(key)
        if not isinstance(value,str) or not value.strip() or report.get(key)!=value:
            errors.append("manifest binding mismatch: "+key)
        elif key.endswith("_commit") and not re.fullmatch(r"[0-9a-f]{40}",value):
            errors.append("invalid full commit hash: "+key)
        elif key=="guide_sha256" and not re.fullmatch(r"[0-9a-f]{64}",value):
            errors.append("invalid guide digest")
    cases = manifest.get("cases")
    if not isinstance(cases,list) or not cases:
        return errors + ["empty qualification manifest"]
    expected = {}
    for case in cases:
        if not isinstance(case,dict):
            errors.append("invalid manifest case")
            continue
        cid = case.get("case_id")
        if not isinstance(cid,str) or not cid.strip() or cid in expected:
            errors.append("invalid or duplicate manifest case ID")
            continue
        if any(not isinstance(case.get(k),str) or not case[k].strip() for k in _FIELDS if k!="energized") or type(case.get("energized")) is not bool:
            errors.append("incomplete manifest case: "+cid)
        expected[cid]=case
    rows=report.get("rows")
    if not isinstance(rows,list):
        return errors+["invalid evidence rows"]
    seen=set()
    for row in rows:
        if not isinstance(row,dict):
            continue
        cid=row.get("case_id")
        if not isinstance(cid,str) or cid not in expected:
            errors.append("unexpected or missing case ID")
            continue
        if cid in seen:
            errors.append("duplicate evidence case: "+cid)
        seen.add(cid)
        if row.get("required") is not True or row.get("result")!="PASS":
            errors.append("manifest case not passed: "+cid)
        for k in _FIELDS:
            if row.get(k)!=expected[cid].get(k) or (k=="energized" and type(row.get(k)) is not bool):
                errors.append("manifest case mismatch: "+cid+" "+k)
        if row.get("energized") is True:
            ref=row.get("independent_safe_state_reference")
            artifacts=row.get("artifacts")
            if not isinstance(ref,str) or not isinstance(artifacts,list) or not any(isinstance(a,dict) and a.get("path")==ref for a in artifacts):
                errors.append("safe-state reference is not a hashed artifact: "+cid)
    for cid in sorted(set(expected)-seen):
        errors.append("missing required manifest case: "+cid)
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report",type=Path)
    parser.add_argument("--artifacts",type=Path,required=True)
    parser.add_argument("--manifest",type=Path,required=True,help="independently approved qualification inventory")
    args=parser.parse_args()
    errors=check_release_evidence(json.loads(args.report.read_text(encoding="utf-8")),json.loads(args.manifest.read_text(encoding="utf-8")),args.artifacts)
    print("\n".join(errors) if errors else "MANIFEST COVERAGE AND STRUCTURE PASSED; technical review still required")
    return int(bool(errors))


if __name__=="__main__":
    raise SystemExit(main())
