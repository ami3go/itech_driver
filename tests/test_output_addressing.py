import pytest
from scpi_driver_core import ConfigurationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("on,token", [(True, "ON"), (False, "OFF"), (1, "ON"), (0, "OFF")])
def test_output_addressing(on, token):
    t = ScriptedScpiTransport().on(f"OUTP:STAT {token}").on("OUTP:STAT?", token)
    with ITM3900D("sim", transport=t) as d:
        assert t.history == []
        d.output.state_set(on)
        assert d.output.state_query() is bool(on)
        assert t.history == [f"OUTP:STAT {token}", "OUTP:STAT?"]


@pytest.mark.parametrize("channel", [0, 2, -1, True, 1.0, "1"])
def test_invalid_channel_no_io(channel):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            d.output.state_set(False, channel=channel)
        with pytest.raises(ConfigurationError):
            d.output.state_query(channel=channel)
        assert t.history == []


@pytest.mark.parametrize("state", [2, -1, "OFF", None, 1.0])
def test_invalid_state_no_io(state):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            d.output.state_set(state)
        assert t.history == []
