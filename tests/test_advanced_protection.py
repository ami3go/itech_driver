import pytest
from scpi_driver_core import ConfigurationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("name,header", [["ovp_delay","VOLT:OVER:PROT:DEL"],["ocp_delay","CURR:OVER:PROT:DEL"],["opp_delay","POW:OVER:PROT:DEL"],["uvp_delay","VOLT:UND:PROT:DEL"],["ucp_delay","CURR:UND:PROT:DEL"],["uvp_warmup","VOLT:UND:PROT:WARM"],["ucp_warmup","CURR:UND:PROT:WARM"]])
def test_protection_times(name, header):
    h = "SOUR:" + header
    t = ScriptedScpiTransport().on(h+"? MIN","0").on(h+"? MAX","10").on(h+" 2.5").on(h+"?","2.5")
    with ITM3900D("sim", transport=t) as d:
        getattr(d.source,name+"_set")(2.5)
        assert getattr(d.source,name+"_query")() == 2.5
        with pytest.raises(ConfigurationError):
            getattr(d.source,name+"_set")(11)
        assert t.history == [h+"? MIN",h+"? MAX",h+" 2.5",h+"?",h+"? MIN",h+"? MAX"]


@pytest.mark.parametrize("name,quantity", [("uvp","VOLT"),("ucp","CURR")])
def test_under_protection(name, quantity):
    h = f"SOUR:{quantity}:UND:PROT"
    t = ScriptedScpiTransport().on(h+":LEV 2").on(h+":LEV?","2").on(h+":STAT 1").on(h+":STAT?","1")
    with ITM3900D("sim", transport=t) as d:
        getattr(d.source,name+"_set")(2)
        assert getattr(d.source,name+"_query")() == 2
        getattr(d.source,name+"_enable")(True)
        assert getattr(d.source,name+"_enable_query")()
        assert t.history == [h+":LEV 2",h+":LEV?",h+":STAT 1",h+":STAT?"]
        with pytest.raises(ConfigurationError):
            getattr(d.source,name+"_enable")("OFF")
        assert len(t.history) == 4
