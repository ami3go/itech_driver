import pytest
from scpi_driver_core import ConfigurationError, ResponseParseError, UnsupportedOperationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


def test_battery_mode_is_selection_not_start():
    t = ScriptedScpiTransport().on("SOUR:FUNC:MODE BATT").on("SOUR:FUNC:MODE?", "BATTERY")
    with ITM3900D("sim", transport=t) as d:
        d.battery.mode_set("BATT")
        assert d.battery.mode_query() == "BATT"
        assert t.history == ["SOUR:FUNC:MODE BATT", "SOUR:FUNC:MODE?"]


def test_unsupported_execution_and_invalid_mode_no_io():
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        for mode in ("CHAR", "DISCH", "BATT;*RST"):
            with pytest.raises(ConfigurationError):
                d.battery.mode_set(mode)
        with pytest.raises(UnsupportedOperationError):
            d.battery.state_set(True)
        with pytest.raises(UnsupportedOperationError):
            d.battery.state_query()
        assert t.history == []


def test_invalid_mode_response():
    t = ScriptedScpiTransport().on("SOUR:FUNC:MODE?", "UNKNOWN")
    with ITM3900D("sim", transport=t) as d, pytest.raises(ResponseParseError):
        d.battery.mode_query()
