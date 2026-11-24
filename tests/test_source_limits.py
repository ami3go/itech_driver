import pytest
from scpi_driver_core import ConfigurationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("name,header", [("voltage_limit","VOLT"),("current_limit","CURR"),("programmed_power_limit","POW")])
def test_limit_range_and_readback(name, header):
    h = f"SOUR:{header}:LIM"
    t = ScriptedScpiTransport().on("*IDN?", "ITECH,IT-M3902D-80-40,SIM,1").on(h+"? MIN","1").on(h+"? MAX","10").on(h+"? DEF","2").on(h+" 5").on(h+"?","5")
    with ITM3900D("sim", transport=t) as d:
        setter = getattr(d.source, name+"_set")
        query = getattr(d.source, name+"_query")
        setter(5)
        assert query() == 5
        assert query(bound="DEF") == 2
        with pytest.raises(ConfigurationError):
            setter(11)
        assert t.history == ["*IDN?", h+"? MIN",h+"? MAX",h+" 5",h+"?",h+"? DEF",h+"? MIN",h+"? MAX"]
        with pytest.raises(ConfigurationError):
            setter(float("nan"))
        with pytest.raises(ConfigurationError):
            query(bound="MAX;*RST")
        assert t.history[-1] == h+"? MAX"
