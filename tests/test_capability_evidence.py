import pytest
from itech_driver import GenericSCPIInstrument
from scpi_driver_core import IdentityError
from scpi_driver_core.simulation import ScriptedScpiTransport


def test_unknown_capabilities_no_probe():
    t=ScriptedScpiTransport().on("SOUR:VOLT?","12")
    with GenericSCPIInstrument("sim",transport=t) as d:
        assert all(v is None for v in d.detect_capabilities().values())
        assert d.is_command_supported("SOUR:VOLT?") is None
        assert d.source is None and d.output is None
        assert t.history==[]


def test_identity_is_fresh_and_capabilities_unknown():
    replies=iter(["ITECH,UNKNOWN,S,1.0","OTHER,UNKNOWN,T,2.0"])
    t=ScriptedScpiTransport().on("*IDN?",lambda _:next(replies))
    with GenericSCPIInstrument("sim",transport=t) as d:
        assert d.get_instrument_info()["serial"]=="S"
        info=d.get_instrument_info()
        assert info["serial"]=="T"
        assert all(v is None for v in info["capabilities"].values())
        assert t.history==["*IDN?","*IDN?"]


def test_invalid_identity_no_capability_claim():
    t=ScriptedScpiTransport().on("*IDN?","bad")
    with GenericSCPIInstrument("sim",transport=t) as d,pytest.raises(IdentityError):
        d.get_instrument_info()


@pytest.mark.parametrize("cmd",["*RST","SOUR:VOLT?;*RST",None])
def test_invalid_probe_no_io(cmd):
    t=ScriptedScpiTransport()
    with GenericSCPIInstrument("sim",transport=t) as d:
        with pytest.raises(ValueError):
            d.is_command_supported(cmd)
        assert t.history==[]
