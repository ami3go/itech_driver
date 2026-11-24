import pytest
from scpi_driver_core import ConfigurationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("quantity,header", [("voltage", "SOUR:VOLT"), ("current", "SOUR:CURR")])
def test_single_output_setpoint(quantity, header):
    t = ScriptedScpiTransport().on(f"{header} 2.5").on(f"{header}?", "2.5")
    with ITM3900D("sim", transport=t) as d:
        getattr(d.source, quantity + "_set")(2.5)
        assert getattr(d.source, quantity + "_query")(channel=1) == 2.5
        assert t.history == [f"{header} 2.5", f"{header}?"]


@pytest.mark.parametrize("quantity", ["voltage", "current"])
@pytest.mark.parametrize("channel", [0, 2, -1, True, 1.0, "1"])
def test_invalid_channel_has_no_io(quantity, channel):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            getattr(d.source, quantity + "_set")(1.0, channel=channel)
        with pytest.raises(ConfigurationError):
            getattr(d.source, quantity + "_query")(channel=channel)
        assert t.history == []


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), -1, True, "1;*RST"])
@pytest.mark.parametrize("quantity", ["voltage", "current"])
def test_invalid_setpoint_has_no_io(quantity, value):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            getattr(d.source, quantity + "_set")(value)
        assert t.history == []
