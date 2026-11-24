import pytest
from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("name,header", [("voltage","VOLT"),("current","CURR"),("power","POW")])
def test_array(name, header):
    cmd = f"MEAS:ARR:{header}?"
    t = ScriptedScpiTransport().on(cmd,"1.25,2.5,3.75")
    with ITM3900D("sim", transport=t) as d:
        query = getattr(d.measurement,name+"_array_query")
        with pytest.raises(ConfigurationError):
            query()
        assert t.history == []
        assert query(ascii_confirmed=True,expected_points=3) == [1.25,2.5,3.75]
        assert t.history == [cmd]


@pytest.mark.parametrize("raw", ["", "1,,3", "1,2,", "1,NaN,3", "1,bad,3", "1,2"])
def test_invalid_array(raw):
    t = ScriptedScpiTransport().on("MEAS:ARR:VOLT?",raw)
    with ITM3900D("sim", transport=t) as d, pytest.raises(ResponseParseError):
        d.measurement.voltage_array_query(ascii_confirmed=True,expected_points=3)
