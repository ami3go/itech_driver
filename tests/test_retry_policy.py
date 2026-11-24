import ast
from pathlib import Path
import pytest
from scpi_driver_core import ConfigurationError, UnsupportedOperationError, TransportTimeoutError
from scpi_driver_core.execution.retry import RetryPolicy
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D
from itech_driver.utils.retry import retry, query_identity_with_retry


def test_generic_decorator_cannot_authorize_arbitrary_replay():
    called = []
    def write():
        called.append(1)
    with pytest.raises(UnsupportedOperationError):
        retry(max_attempts=3)(write)
    assert called == []


def test_core_safe_identity_retry_is_explicit_and_bounded():
    calls = []
    def reply(_):
        calls.append(1)
        if len(calls) == 1:
            raise TransportTimeoutError("first response lost")
        return "ITECH,IT-M3902D-80-40,S,1"
    t = ScriptedScpiTransport().on("*IDN?", reply)
    with ITM3900D("sim", transport=t) as d:
        initial_generation = d.session.generation
        policy = RetryPolicy(attempts=2, max_elapsed_s=1)
        assert query_identity_with_retry(d, policy=policy).startswith("ITECH,")
        assert d.session.generation > initial_generation
        assert t.history == ["*IDN?", "*IDN?"]


@pytest.mark.parametrize("policy", [None, RetryPolicy(attempts=True), RetryPolicy(attempts=1.5),
                                   RetryPolicy(attempts=2)])
def test_invalid_retry_budget_no_io(policy):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            query_identity_with_retry(d, policy=policy)
    assert t.history == []


def test_no_legacy_retry_call_sites_in_package():
    import itech_driver
    root = Path(itech_driver.__file__).parent
    for path in root.rglob("*.py"):
        if path == root / "utils" / "retry.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not any(a.name == "retry" for a in node.names), path
            if isinstance(node, ast.Import):
                assert not any(a.name.endswith("utils.retry") for a in node.names), path
            if isinstance(node, ast.Call):
                assert not (isinstance(node.func, ast.Name) and node.func.id == "retry"), path


def test_retry_refresh_updates_cached_identity_and_revokes_remote():
    t = ScriptedScpiTransport().on("*IDN?", "ITECH,IT-M3902D-80-40,S1,1").on("SYST:REM")
    with ITM3900D("sim", transport=t, require_remote=True) as d:
        d.enter_remote()
        d.identity_snapshot()
        calls = []
        def reply(_):
            calls.append(1)
            if len(calls) == 1:
                raise TransportTimeoutError("lost")
            return "ITECH,IT-M3902D-80-40,S2,1"
        t.on("*IDN?", reply)
        query_identity_with_retry(d, policy=RetryPolicy(attempts=2, max_elapsed_s=1))
        assert d.identity_snapshot().serial_number == "S2"
        assert d.requested_mode is None
        assert t.history == ["SYST:REM", "*IDN?", "*IDN?", "*IDN?"]
