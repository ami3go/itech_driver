import pytest
from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("arg,wire,reply,expected", [(True,1,"IN",True),(False,0,"OUT",False),("IN",1,"1",True),("OUT",0,"0",False)])
def test_direction(arg, wire, reply, expected):
    t = ScriptedScpiTransport().on(f"IO:DIRE 0,{wire}").on("IO:DIRE? 0", reply)
    with ITM3900D("sim", transport=t) as d:
        d.io.direction_set("0", arg)
        assert d.io.direction_query(0) is expected
        assert t.history == [f"IO:DIRE 0,{wire}", "IO:DIRE? 0"]


def test_invalid_direction_and_pin():
    t = ScriptedScpiTransport().on("IO:DIRE? 0", "ON")
    with ITM3900D("sim", transport=t) as d:
        for pin in ("1,2", "0;*RST", 7, -1, True):
            with pytest.raises(ConfigurationError):
                d.io.direction_set(pin, True)
        with pytest.raises(ConfigurationError):
            d.io.direction_set(0, "ON")
        assert t.history == []
        with pytest.raises(ResponseParseError):
            d.io.direction_query(0)
