import pytest
from itech_driver import ITM3900D
from scpi_driver_core import ConfigurationError
from scpi_driver_core.simulation import ScriptedScpiTransport


def test_cv_resistance_range_and_readback():
    t=ScriptedScpiTransport().on("SOUR:FUNC?","VOLT").on("SOUR:RES? MIN","0").on("SOUR:RES? MAX","0.5").on("SOUR:RES 0.1").on("SOUR:RES?","0.1")
    with ITM3900D("sim",transport=t) as d:
        d.source.resistance_set(0.1)
        assert d.source.resistance_query()==0.1
        assert d.source.resistance_query(bound="MAX")==0.5
        with pytest.raises(ConfigurationError):
            d.source.resistance_set(0.6)
        assert t.history==["SOUR:FUNC?","SOUR:RES? MIN","SOUR:RES? MAX","SOUR:RES 0.1",
                           "SOUR:FUNC?","SOUR:RES?","SOUR:FUNC?","SOUR:RES? MAX",
                           "SOUR:FUNC?","SOUR:RES? MIN","SOUR:RES? MAX"]


def test_cc_rejects_resistance_without_mode_change():
    t=ScriptedScpiTransport().on("SOUR:FUNC?","CURR")
    with ITM3900D("sim",transport=t) as d:
        with pytest.raises(ConfigurationError):
            d.source.resistance_set(0.1)
        with pytest.raises(ConfigurationError):
            d.source.resistance_query()
        assert t.history==["SOUR:FUNC?","SOUR:FUNC?"]


@pytest.mark.parametrize("value",[-1,float("nan"),float("inf"),True])
def test_bad_resistance_no_io(value):
    t=ScriptedScpiTransport()
    with ITM3900D("sim",transport=t) as d:
        with pytest.raises(ConfigurationError):
            d.source.resistance_set(value)
        assert t.history==[]
