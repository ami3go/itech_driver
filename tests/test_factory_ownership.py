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
    ("IT-M3902D-80-40", ITM3900D, 2),
    ("UNKNOWN", GenericSCPIInstrument, 1),
])
def test_factory_ownership(model,expected,opens):
    t = CountingTransport().on("*IDN?",f"ITECH,{model},S,1.0")
    with auto_detect_instrument("sim",transport=t) as driver:
        assert isinstance(driver,expected)
        assert t.opens == opens
        assert t.closes == opens-1
    assert t.opens == t.closes == opens
    assert not t.active


def test_parse_failure_closes_probe():
    t = CountingTransport().on("*IDN?","bad")
    with pytest.raises(IdentityError):
        auto_detect_instrument("sim",transport=t)
    assert t.opens == t.closes == 1
