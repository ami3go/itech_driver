import pytest
from scpi_driver_core import ConfigurationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("name,header", [["voltage_rise_time","SOUR:VOLT:SLEW:POS"],["voltage_fall_time","SOUR:VOLT:SLEW:NEG"],["voltage_both_time","SOUR:VOLT:SLEW:BOTH"],["current_rise_time","SOUR:CURR:SLEW:POS"],["current_fall_time","SOUR:CURR:SLEW:NEG"],["current_both_time","SOUR:CURR:SLEW:BOTH"]])
def test_slew_time(name,header):
    t = ScriptedScpiTransport().on(header+"? MIN","0.001").on(header+"? MAX","10").on(header+" 0.1").on(header+"?","0.1")
    with ITM3900D("sim",transport=t) as d:
        getattr(d.source,name+"_set")(0.1)
        assert getattr(d.source,name+"_query")() == 0.1
        with pytest.raises(ConfigurationError):
            getattr(d.source,name+"_set")(11)
        assert t.history == [header+"? MIN",header+"? MAX",header+" 0.1",header+"?",header+"? MIN",header+"? MAX"]
