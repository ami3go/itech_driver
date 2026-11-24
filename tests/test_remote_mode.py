import pytest
from scpi_driver_core import SafetyGuardError, TransportTimeoutError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D
from itech_driver.exceptions import TimeoutError


def fixture():
    return (ScriptedScpiTransport().on("SYST:REM").on("SYST:LOC")
            .on("SOUR1:VOLT 1").on("*IDN?", "ITECH,IT-M3900D,SIM,1")
            .on("*RST"))


def test_remote_guard_and_context_order():
    t = fixture()
    with ITM3900D("sim", transport=t, require_remote=True) as d:
        assert d.requested_mode is None
        assert d.identify().startswith("ITECH")
        with pytest.raises(SafetyGuardError):
            d.source.voltage_set(1)
        with d.remote_mode():
            assert d.requested_mode == "remote"
            d.source.voltage_set(1)
        assert d.requested_mode == "local"
    assert t.history == ["*IDN?", "SYST:REM", "SOUR1:VOLT 1", "SYST:LOC"]


def test_system_methods_and_generation():
    t = fixture()
    with ITM3900D("sim", transport=t, require_remote=True) as d:
        d.system.remote()
        assert d.requested_mode == "remote"
        d.session.close()
        d.session.open()
        assert d.requested_mode is None
        with pytest.raises(SafetyGuardError):
            d.source.voltage_set(1)
        d.system.remote()
        d.ieee.reset()
        assert d.requested_mode is None
        d.system.local()
        assert d.requested_mode == "local"


def test_context_preserves_body_exception():
    t = fixture()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ValueError, match="body"):
            with d.remote_mode():
                raise ValueError("body")
    assert t.history == ["SYST:REM", "SYST:LOC"]


def test_failed_remote_never_enables_guard():
    t = fixture()
    def fail(_):
        raise TransportTimeoutError("ambiguous")
    t.on("SYST:REM", fail)
    with ITM3900D("sim", transport=t, require_remote=True) as d:
        with pytest.raises(TimeoutError):
            d.enter_remote()
        assert d.requested_mode is None
        with pytest.raises(SafetyGuardError):
            d.source.voltage_set(1)
    assert t.history == ["SYST:REM"]
