"""Offline structural HIL evidence checker. Never contacts hardware."""
import argparse
import hashlib
import json
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
        identity=tuple(str(row.get(k,"")) for k in ("model","serial","firmware","interface","command"))
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
        if row.get("energized") is True and not row.get("independent_safe_state_reference"):
            errors.append(prefix+"missing independent safe-state reference")
    if required==0:
        errors.append("no required qualification rows")
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report",type=Path)
    parser.add_argument("--artifacts",type=Path,required=True)
    args=parser.parse_args()
    errors=check_evidence(json.loads(args.report.read_text(encoding="utf-8")),args.artifacts)
    print("\n".join(errors) if errors else "STRUCTURAL CHECK PASSED; technical review still required")
    return int(bool(errors))


if __name__=="__main__":
    raise SystemExit(main())
