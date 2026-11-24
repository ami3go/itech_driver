import pytest
from itech_driver import ITM3900D
from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport


@pytest.mark.parametrize("quantity,header",[("voltage","SOUR:VOLT"),("current","SOUR:CURR")])
@pytest.mark.parametrize("lo,hi,value",[("0","5",6),("2","5",1),("5","2",3)])
def test_outside_range_no_setting_write(quantity,header,lo,hi,value):
    t=ScriptedScpiTransport().on(header+"? MIN",lo).on(header+"? MAX",hi)
    with ITM3900D("sim",transport=t) as d:
        with pytest.raises(ConfigurationError):
            getattr(d.source,quantity+"_set")(value)
        assert t.history==[header+"? MIN",header+"? MAX"]


def test_malformed_bound_no_setting_write():
    t=ScriptedScpiTransport().on("SOUR:VOLT? MIN","bad")
    with ITM3900D("sim",transport=t) as d,pytest.raises(ResponseParseError):
        try:
            d.source.voltage_set(1)
        finally:
            assert t.history==["SOUR:VOLT? MIN"]
