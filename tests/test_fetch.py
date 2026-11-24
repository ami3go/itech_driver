import pytest
from scpi_driver_core import ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D
from itech_driver.exceptions import TimeoutError


@pytest.mark.parametrize("method,command", [["voltage_query","FETC:VOLT?"],["voltage_high_query","FETC:VOLT:HIGH?"],["voltage_low_query","FETC:VOLT:LOW?"],["voltage_max_query","FETC:VOLT:MAX?"],["voltage_min_query","FETC:VOLT:MIN?"],["current_query","FETC:CURR?"],["current_high_query","FETC:CURR:HIGH?"],["current_low_query","FETC:CURR:LOW?"],["current_max_query","FETC:CURR:MAX?"],["current_min_query","FETC:CURR:MIN?"],["power_query","FETC:POW?"],["power_max_query","FETC:POW:MAX?"],["power_min_query","FETC:POW:MIN?"]])
def test_scalar_fetch(method,command):
    t = ScriptedScpiTransport().on(command,"2.5")
    with ITM3900D("sim", transport=t) as d:
        assert getattr(d.fetch,method)() == 2.5
        assert t.history == [command]


@pytest.mark.parametrize("name,header", [("voltage","VOLT"),("current","CURR"),("power","POW")])
def test_fetch_array(name,header):
    cmd = f"FETC:ARR:{header}?"
    t = ScriptedScpiTransport().on(cmd,"1,2,3")
    with ITM3900D("sim", transport=t) as d:
        assert getattr(d.fetch,name+"_array_query")(ascii_confirmed=True,expected_points=3) == [1,2,3]
        assert t.history == [cmd]


def test_fetch_timeout_does_not_trigger_or_replay():
    from scpi_driver_core.simulation import ScriptedReply
    from scpi_driver_core.exceptions import TransportTimeoutError
    t = ScriptedScpiTransport().on("FETC:VOLT?",ScriptedReply(raises=TransportTimeoutError("not ready")))
    with ITM3900D("sim", transport=t) as d, pytest.raises(TimeoutError):
        try:
            d.fetch.voltage_query()
        finally:
            assert t.history == ["FETC:VOLT?"]


def test_bad_fetch():
    t = ScriptedScpiTransport().on("FETC:ARR:VOLT?","1,,3")
    with ITM3900D("sim", transport=t) as d, pytest.raises(ResponseParseError):
        d.fetch.voltage_array_query(ascii_confirmed=True,expected_points=3)
