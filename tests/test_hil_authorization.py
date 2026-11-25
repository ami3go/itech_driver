import json
from pathlib import Path
import subprocess
import sys

import pytest

from itech_driver.hil_authorization import enroll, issue, validate, validate_config, pytest_arguments, validate_pytest, TTL


@pytest.fixture
def bench():
    return dict(bench_id="synthetic", operator="offline-test", model="synthetic",
                serial="not-real", firmware="synthetic", address="192.0.2.1",
                guide_reference="synthetic", safe_state_reference="synthetic",
                emergency_reference="synthetic", interface="tcp",
                bench_available=True, attended=True, independent_output_off=True,
                dc_isolated=True, emergency_ready=True, energized=False,
                remote_local=False, timeout_ms=2000, tcp_port=12345,
                baudrate=9600, bytesize=8, parity="N", stopbits=1, termination="lf")


@pytest.fixture
def permit(tmp_path, bench):
    authority, key = tmp_path / "authority", tmp_path / "key"
    enroll(authority, "123456")
    issue(authority, bench, key, "123456", now=1000)
    return authority, key


def test_validity_scope_and_expiry(bench, permit):
    authority, key = permit
    assert validate(authority, bench, key, now=1000)
    assert validate(authority, bench, key, now=1000+TTL-1)
    for now in (999, 1000+TTL):
        with pytest.raises(ValueError):
            validate(authority, bench, key, now=now)
    for field, value in (("serial", "different"), ("remote_local", True), ("energized", True)):
        with pytest.raises(ValueError):
            validate(authority, dict(bench, **{field: value}), key, now=1000)


def test_tamper_and_wrong_pin(tmp_path, bench, permit):
    authority, key = permit
    with pytest.raises(ValueError):
        issue(authority, bench, tmp_path / "bad", "654321", now=1000)
    assert not (tmp_path / "bad").exists()
    record = json.loads(key.read_text())
    record["payload"]["expires"] += 1
    key.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        validate(authority, bench, key, now=1000)


def test_prerequisite_and_scope(bench):
    for field in ("attended", "independent_output_off", "dc_isolated", "emergency_ready"):
        with pytest.raises(ValueError):
            validate_config(dict(bench, **{field: False}))
    args = pytest_arguments(bench)
    assert "--hil-remote-local" not in args
    options = dict(zip(args[::2], args[1::2]))
    for name in ("timeout", "tcp-port", "baudrate", "bytesize", "stopbits"):
        options["--hil-" + name] = int(options["--hil-" + name])
    options["--hil-remote-local"] = False
    validate_pytest(bench, options.get)
    options["--hil-address"] = "other"
    with pytest.raises(ValueError):
        validate_pytest(bench, options.get)


def test_runner_no_io_modes():
    root = Path(__file__).resolve().parents[1]
    runner = root / "scripts/hil/run_hil.py"
    for args in (["--list"], ["--dry-run", "--suite", "full"]):
        result = subprocess.run([sys.executable, str(runner), *args], capture_output=True,
                                text=True, cwd=root, check=True)
        assert json.loads(result.stdout)
    result = subprocess.run([sys.executable, str(runner), "--suite", "source"],
                            capture_output=True, text=True, cwd=root)
    assert result.returncode == 2
    assert "BLOCKED" in result.stderr
