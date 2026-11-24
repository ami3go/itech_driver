import pytest
from scpi_driver_core import ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("method,command", [["voltage_query","MEAS:VOLT?"],["voltage_high_query","MEAS:VOLT:HIGH?"],["voltage_low_query","MEAS:VOLT:LOW?"],["voltage_max_query","MEAS:VOLT:MAX?"],["voltage_min_query","MEAS:VOLT:MIN?"],["current_query","MEAS:CURR?"],["current_high_query","MEAS:CURR:HIGH?"],["current_low_query","MEAS:CURR:LOW?"],["current_max_query","MEAS:CURR:MAX?"],["current_min_query","MEAS:CURR:MIN?"],["power_query","MEAS:POW?"],["power_max_query","MEAS:POW:MAX?"],["power_min_query","MEAS:POW:MIN?"]])
def test_measurement_wire(method, command):
    t = ScriptedScpiTransport().on(command, "1.25E1")
    with ITM3900D("sim", transport=t) as d:
        assert getattr(d.measurement, method)() == 12.5
        assert t.history == [command]


@pytest.mark.parametrize("reply", ["bad", "NaN", "Inf"])
def test_bad_measurement(reply):
    t = ScriptedScpiTransport().on("MEAS:VOLT?", reply)
    with ITM3900D("sim", transport=t) as d, pytest.raises(ResponseParseError):
        d.measurement.voltage_query()
