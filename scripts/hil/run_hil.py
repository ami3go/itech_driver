"""Single entry point for implemented HIL procedures; no I/O for list/dry-run."""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import platform
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "docs/hil/test_matrix.json"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    action = p.add_mutually_exclusive_group()
    action.add_argument("--list", action="store_true")
    action.add_argument("--dry-run", action="store_true")
    action.add_argument("--preflight", action="store_true")
    p.add_argument("--suite", default="communication")
    p.add_argument("--config")
    p.add_argument("--authority")
    p.add_argument("--key")
    p.add_argument("--evidence")
    a = p.parse_args(argv)
    cases = json.loads(CATALOG.read_text(encoding="utf-8"))
    if a.list:
        print(json.dumps(cases, indent=2))
        return 0
    selected = [c for c in cases if a.suite == "full" or a.suite == c["suite"] or a.suite == c["id"]
                or (a.suite == "smoke" and c["id"] == "HIL-COM-ID")]
    if not selected:
        p.error("unknown suite or case")
    if a.dry_run:
        print(json.dumps({"physical_io": False, "selected": selected}, indent=2))
        return 0
    if not all(c["automated"] for c in selected) and not a.preflight:
        p.exit(2, "BLOCKED: selected suite includes unimplemented procedures; no hardware contacted.\n")
    if not (a.config and a.authority and a.key):
        p.error("--config, --authority and --key required")
    from itech_driver.hil_authorization import read_object, validate, pytest_arguments, digest_config
    try:
        config = read_object(a.config)
        for path in (a.authority, a.key):
            if Path(path).resolve().is_relative_to(ROOT):
                raise ValueError("authorization files must be external")
        validate(a.authority, config, a.key)
        args = pytest_arguments(config)
    except (ValueError, OSError, KeyError):
        p.exit(2, "BLOCKED: bench preflight or authorization failed; no hardware contacted.\n")
    if a.preflight:
        print("Local configuration and permit accepted; physical readiness NOT VERIFIED.")
        return 0
    if not a.evidence:
        p.error("--evidence must be a new output directory")
    if any(c["id"] == "HIL-COM-REMOTE" for c in selected) and not config["remote_local"]:
        p.exit(2, "BLOCKED: remote/local not in approved scope.\n")
    evidence = Path(a.evidence).resolve()
    evidence.mkdir(parents=True, exist_ok=False)
    names = {"HIL-COM-ID": "test_physical_read_only_identity",
             "HIL-COM-REMOTE": "test_physical_remote_local"}
    nodes = ["tests/test_hardware_interfaces.py::" + names[c["id"]] for c in selected]
    cmd = [sys.executable, "-m", "pytest", "-m", "hardware", "--run-hil",
           "--hil-config", str(Path(a.config).resolve()),
           "--hil-authority", str(Path(a.authority).resolve()),
           "--hil-key", str(Path(a.key).resolve()), "-x",
           "--junitxml", str(evidence / "results.xml"), *args, *nodes]
    print("Communication-only run. Operator must independently verify final safe state.")
    def version(package):
        try:
            return importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            return None

    meta = {"evidence_type": "physical", "execution_status": "INCONCLUSIVE",
            "start_utc": datetime.now(timezone.utc).isoformat(),
            "end_utc": None, "exit_code": None,
            "driver_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "driver_version": version("itech-itm3900d-driver"),
            "core_version": version("scpi-driver-core"),
            "python": platform.python_version(), "os": platform.platform(),
            "bench_id": config["bench_id"], "model": config["model"], "serial": config["serial"],
            "firmware": config["firmware"], "interface": config["interface"],
            "operator": config["operator"], "config_sha256": digest_config(config),
            "authorization_validated": True, "cases": [c["id"] for c in selected],
            "final_safe_state": "UNVERIFIED: independent operator evidence required"}
    def save_metadata():
        (evidence / "execution.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    save_metadata()
    try:
        result = subprocess.run(cmd, cwd=ROOT, check=False)
        meta["exit_code"] = result.returncode
    finally:
        meta["end_utc"] = datetime.now(timezone.utc).isoformat()
        save_metadata()
    print("JUnit is execution evidence, not a physical qualification verdict.")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
