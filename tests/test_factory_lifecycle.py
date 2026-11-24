import pytest
from itech_driver import auto_detect_instrument, ITM3900D, GenericSCPIInstrument
from scpi_driver_core import IdentityError
from scpi_driver_core.simulation import ScriptedScpiTransport


class CountingTransport(ScriptedScpiTransport):
    def __init__(self):
        super().__init__()
        self.events = []
    def open(self):
        self.events.append("open")
        return super().open()
    def close(self):
        self.events.append("close")
        return super().close()


@pytest.mark.parametrize("model,cls,events",[
    ("IT-M3902D-80-40",ITM3900D,["open","close","open"]),
    ("UNKNOWN",GenericSCPIInstrument,["open"])])
def test_factory_ownership(model,cls,events):
    t=CountingTransport().on("*IDN?",f"ITECH,{model},SERIAL,1.0")
    with auto_detect_instrument("sim",transport=t) as d:
        assert isinstance(d,cls)
        assert t.events==events
    assert t.events==events+["close"]


def test_bad_identity_closes_temporary_connection():
    t=CountingTransport().on("*IDN?","bad")
    with pytest.raises(IdentityError):
        auto_detect_instrument("sim",transport=t)
    assert t.events==["open","close"]


def test_identification_failure_keeps_primary(monkeypatch):
    def fail_close(self):
        raise RuntimeError("cleanup failure")
    monkeypatch.setattr(GenericSCPIInstrument,"close",fail_close)
    t=CountingTransport().on("*IDN?","bad")
    with pytest.raises(IdentityError) as exc:
        auto_detect_instrument("sim",transport=t)
    assert isinstance(exc.value.cleanup_error,RuntimeError)
    t.close()
