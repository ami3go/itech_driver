import pytest
from itech_driver import ITM3900D
from itech_driver.subsystems.LoggingSubsystem import LoggingConfig
from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport


def test_dlog_config_plan():
    assert LoggingConfig(True,False,True,0.2,20).commands(
        "DLOG",min_period=0.1,max_period=1,max_duration=100) == (
        "SENS:DLOG:FUNC:VOLT 1","SENS:DLOG:FUNC:CURR 0","SENS:DLOG:FUNC:PEAK 1",
        "SENS:DLOG:PER 0.2","SENS:DLOG:TIME 20")


def test_dlog_status_and_no_speculative_fetch():
    t=ScriptedScpiTransport().on("DLOG:STAT?","0")
    with ITM3900D("sim",transport=t) as d:
        assert d.dlog.state_query()=="0"
        with pytest.raises(ConfigurationError):
            d.dlog.raw_data_query(ascii_confirmed=True)
        assert t.history==["DLOG:STAT?"]


def test_empty_dlog_status():
    t=ScriptedScpiTransport().on("DLOG:STAT?","\n")
    with ITM3900D("sim",transport=t) as d,pytest.raises(ResponseParseError):
        d.dlog.state_query()
