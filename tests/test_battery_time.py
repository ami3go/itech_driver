import pytest
from scpi_driver_core import ConfigurationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("value", [0, 3, 3.25, 20.5])
def test_cutoff_preserves_numeric_precision(value):
    t = ScriptedScpiTransport().on(f"BATT:SHUT:TIME {value}").on("BATT:SHUT:TIME?", str(value))
    with ITM3900D("sim", transport=t) as d:
        d.battery.shutdown_time_set(value)
        assert d.battery.shutdown_time_query() == value
        assert t.history == [f"BATT:SHUT:TIME {value}", "BATT:SHUT:TIME?"]


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True, "1;*RST"])
def test_bad_cutoff_no_io(value):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            d.battery.shutdown_time_set(value)
        assert t.history == []
