import pytest
from itech_driver.subsystems.LoggingSubsystem import LoggingConfig
from itech_driver import ITM3900D
from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport


def test_elog_configuration_plan():
    assert LoggingConfig(True,True,False,0.1,10).commands("ELOG",min_period=0.01,max_period=1,max_duration=100) == (
        "SENS:ELOG:FUNC:VOLT 1","SENS:ELOG:FUNC:CURR 1","SENS:ELOG:FUNC:PEAK 0",
        "SENS:ELOG:PER 0.1","SENS:ELOG:TIME 10")


@pytest.mark.parametrize("cfg",[LoggingConfig(False,False,False,0.1,10),
    LoggingConfig(True,True,False,0,10),LoggingConfig(True,True,False,0.1,0.05)])
def test_invalid_plan(cfg):
    with pytest.raises(ConfigurationError):
        cfg.commands("ELOG",min_period=0.01,max_period=1,max_duration=100)


def test_raw_elog_queries():
    t=ScriptedScpiTransport().on("ELOG:STAT?","0").on("FETC:ELOG:ARR:DATA?","1,2,3")
    with ITM3900D("sim",transport=t) as d:
        assert d.elog.state_query()=="0"
        with pytest.raises(ConfigurationError):
            d.elog.raw_data_query()
        assert d.elog.raw_data_query(ascii_confirmed=True)=="1,2,3"
        assert t.history==["ELOG:STAT?","FETC:ELOG:ARR:DATA?"]
