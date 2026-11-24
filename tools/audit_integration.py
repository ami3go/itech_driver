#!/usr/bin/env python3
"""Offline git integration audit. Never pushes, never executes driver code.

Run ONLY in a disposable git checkout. Fetch PR refs, freeze exact commits,
attempt ordered merges, abort conflicts, and write JSON. No release decision.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

DEFAULT_PRS = [2,3,4,5,6,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,136,138,139,140,141,142,143,144,145,146,147,148]

def git(repo, *args, check=True):
    return subprocess.run(["git","-c","core.hooksPath=/dev/null",
                           "-c","user.name=ITECH integration audit",
                           "-c","user.email=integration-audit@example.invalid",
                           "-C",str(repo),*args],text=True,capture_output=True,check=check,
                          env={**os.environ,"GIT_MERGE_AUTOEDIT":"no","GIT_TERMINAL_PROMPT":"0"})


def sha(repo,ref):
    return git(repo,"rev-parse","--verify",ref+"^{commit}").stdout.strip()


def audit(repo,base,prs,*,fetch=True,archive=None):
    base_sha=sha(repo,base)
    if len(set(prs))!=len(prs) or any(type(n) is not int or n<=0 for n in prs):
        raise ValueError("invalid PR inventory")
    if fetch:
        for start in range(0,len(prs),12):
            git(repo,"fetch","--no-tags","origin",*[
                f"+refs/pull/{n}/head:refs/itech-audit/pr/{n}" for n in prs[start:start+12]])
    heads={n:sha(repo,f"refs/itech-audit/pr/{n}") for n in prs}
    result={"base_sha":base_sha,"heads":{str(n):v for n,v in heads.items()},
            "results":[],"status":"INCOMPLETE"}
    with tempfile.TemporaryDirectory(prefix="itech-integration-") as tmp:
        work=Path(tmp)/"work"
        git(repo,"worktree","add","--detach",str(work),base_sha)
        try:
            for n,head in heads.items():
                if git(work,"merge-base","--is-ancestor",head,"HEAD",check=False).returncode==0:
                    result["results"].append({"pr":n,"sha":head,"status":"ALREADY_INCLUDED"})
                    continue
                before=sha(work,"HEAD")
                merge=git(work,"-c","rerere.enabled=false","merge","--no-ff","--no-edit",head,check=False)
                if merge.returncode:
                    conflicts=git(work,"diff","--name-only","--diff-filter=U",check=False).stdout.splitlines()
                    result["results"].append({"pr":n,"sha":head,"status":"CONFLICT" if conflicts else "MERGE_ERROR",
                                              "files":conflicts,"diagnostic":(merge.stdout+merge.stderr)[-6000:]})
                    # Abort a failed merge. If it did not start, HEAD must still
                    # equal before. Never use a failed partial tree.
                    if git(work,"rev-parse","--verify","MERGE_HEAD",check=False).returncode==0:
                        git(work,"merge","--abort")
                    if sha(work,"HEAD")!=before or git(work,"status","--porcelain").stdout:
                        raise RuntimeError("merge abort did not restore clean worktree")
                else:
                    result["results"].append({"pr":n,"sha":head,"status":"MERGED_IN_AUDIT",
                                              "audit_commit":sha(work,"HEAD")})
            result["audit_tree"]=git(work,"rev-parse","HEAD^{tree}").stdout.strip()
            result["status"]="CONFLICTS" if any(r["status"] in ("CONFLICT","MERGE_ERROR") for r in result["results"]) else "CLEAN_MERGE_AUDIT"
            if archive is not None and result["status"]=="CLEAN_MERGE_AUDIT":
                archive=Path(archive).resolve()
                git(work,"archive","--format=zip","--output="+str(archive),"HEAD")
                result["archive_sha256"]=hashlib.sha256(archive.read_bytes()).hexdigest()
                result["audit_commit"]=sha(work,"HEAD")
        finally:
            git(repo,"worktree","remove","--force",str(work))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path,default=Path("."))
    parser.add_argument("--base",required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--prs",nargs="+",type=int,default=DEFAULT_PRS)
    parser.add_argument("--archive",type=Path)
    args=parser.parse_args()
    report=audit(args.repo.resolve(),args.base,args.prs,archive=args.archive)
    args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    for r in report["results"]:
        print(f'PR #{r["pr"]}: {r["status"]} {", ".join(r.get("files",[]))}')
    print(report["status"],"— no branches pushed; no driver tests executed")
    return 0 if report["status"]=="CLEAN_MERGE_AUDIT" else 1


if __name__=="__main__":
    raise SystemExit(main())
