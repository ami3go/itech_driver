import pytest
from itech_driver import auto_detect_instrument, ITM3900D, GenericSCPIInstrument
from scpi_driver_core import IdentityError
from scpi_driver_core.simulation import ScriptedScpiTransport


class CountingTransport(ScriptedScpiTransport):
    def __init__(self):
        super().__init__()
        self.opens = self.closes = 0
        self.active = False

    def open(self):
        assert not self.active, "overlapping ownership"
        super().open()
        self.active = True
        self.opens += 1

    def close(self):
        if self.active:
            self.closes += 1
            self.active = False
        return super().close()


@pytest.mark.parametrize("model,expected,opens",[
    ("IT-M3902D-80-40", ITM3900D, 1),
    ("UNKNOWN", GenericSCPIInstrument, 1),
])
def test_factory_ownership(model,expected,opens):
    t = CountingTransport().on("*IDN?",f"ITECH,{model},S,1.0")
    with auto_detect_instrument("sim",transport=t) as driver:
        assert isinstance(driver,expected)
        assert t.opens == opens
        assert t.closes == opens-1
        assert t.history == ["*IDN?"]
        assert driver.identity_snapshot().model == model
        assert t.history == ["*IDN?"]
    assert t.opens == t.closes == opens
    assert not t.active


def test_parse_failure_closes_probe():
    t = CountingTransport().on("*IDN?","bad")
    with pytest.raises(IdentityError):
        auto_detect_instrument("sim",transport=t)
    assert t.opens == t.closes == 1


def test_non_reopenable_injected_transport_adopted_once():
    class NonReopenable(CountingTransport):
        def open(self):
            assert self.opens == 0, "transport cannot reopen"
            return super().open()

    from itech_driver.capabilities import ApplicationLimits, Range
    from scpi_driver_core import SafetyGuardError
    t = NonReopenable().on("*IDN?", "ITECH,IT-M3902D-80-40,S,1")
    app = ApplicationLimits(voltage=Range(0, 5))
    with auto_detect_instrument("sim", transport=t, require_remote=True, application_limits=app) as d:
        assert isinstance(d, ITM3900D)
        assert d.application_limits is app
        assert d.requested_mode is None
        assert t.opens == 1 and t.closes == 0
        with pytest.raises(SafetyGuardError):
            d.source.voltage_set(1)
        assert t.history == ["*IDN?"]
    assert t.opens == t.closes == 1


def test_unknown_identity_cannot_discard_requested_remote_policy():
    t = CountingTransport().on("*IDN?", "OTHER,UNKNOWN,S,1")
    with pytest.raises(IdentityError):
        auto_detect_instrument("sim", transport=t, require_remote=True)
    assert t.opens == t.closes == 1
    assert t.history == ["*IDN?"]


def test_failed_adoption_closes_probe(monkeypatch):
    t = CountingTransport().on("*IDN?", "ITECH,IT-M3902D-80-40,S,1")
    def fail(self):
        raise RuntimeError("subsystem binding failed")
    monkeypatch.setattr(ITM3900D, "_initialize_subsystems", fail)
    with pytest.raises(RuntimeError, match="subsystem binding failed"):
        auto_detect_instrument("sim", transport=t)
    assert t.opens == t.closes == 1
    assert t.history == ["*IDN?"]
