import pytest
from scpi_driver_core import SafetyGuardError, TransportTimeoutError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D
from itech_driver.exceptions import TimeoutError


def fixture():
    return (ScriptedScpiTransport().on("SYST:REM").on("SYST:LOC")
            .on("SOUR:VOLT? MIN", "0").on("SOUR:VOLT? MAX", "10")
            .on("SOUR:VOLT 1").on("*IDN?", "ITECH,IT-M3902D-80-40,SIM,1")
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
    assert t.history == ["*IDN?", "SYST:REM", "*IDN?", "SOUR:VOLT? MIN", "SOUR:VOLT? MAX", "SOUR:VOLT 1", "SYST:LOC"]


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
        assert t.history == ["SYST:REM"]
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
        assert t.state.name == "FAULTED"
        with pytest.raises(SafetyGuardError):
            d.source.voltage_set(1)
        with pytest.raises(SafetyGuardError):
            d.output.state_set(True)
        assert t.state.name == "FAULTED"
        assert t.history == ["SYST:REM"]
        d.session.close()
        d.session.open()
        assert d.requested_mode is None
        with pytest.raises(SafetyGuardError):
            d.output.state_set(True)
    assert t.history == ["SYST:REM"]


def test_missing_range_terminator_invalidates_remote_authorization():
    t = fixture().on("SOUR:VOLT? MIN", b"0")
    with ITM3900D("sim", transport=t, require_remote=True) as d:
        d.enter_remote()
        with pytest.raises(TimeoutError):
            d.source.voltage_set(1)
        assert d.requested_mode is None
        assert t.state.name == "FAULTED"
        with pytest.raises(SafetyGuardError):
            d.output.state_set(True)
        assert t.history == ["SYST:REM", "*IDN?", "SOUR:VOLT? MIN"]


def test_fragmented_range_reply_preserves_exact_order():
    t = fixture()
    def fragmented(_):
        t.inner.feed(b"0")
        return b"\n"
    t.on("SOUR:VOLT? MIN", fragmented)
    with ITM3900D("sim", transport=t, require_remote=True) as d:
        d.enter_remote()
        d.source.voltage_set(1)
    assert t.history == ["SYST:REM", "*IDN?", "SOUR:VOLT? MIN", "SOUR:VOLT? MAX", "SOUR:VOLT 1"]
