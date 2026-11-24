import pytest
from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("loop", ["cv","cc"])
@pytest.mark.parametrize("speed", ["HIGH","LOW"])
def test_loop_speed(loop,speed):
    header = f"SOUR:{loop.upper()}:PRI"
    t = ScriptedScpiTransport().on(f"{header} {speed}").on(header+"?",speed)
    with ITM3900D("sim",transport=t) as d:
        getattr(d.source,loop+"_loop_speed_set")(speed.lower())
        assert getattr(d.source,loop+"_loop_speed_query")() == speed
        assert t.history == [f"{header} {speed}",header+"?"]


def test_bad_speed():
    t = ScriptedScpiTransport().on("SOUR:CV:PRI?","FAST")
    with ITM3900D("sim",transport=t) as d:
        with pytest.raises(ConfigurationError):
            d.source.cv_loop_speed_set("HIGH;*RST")
        assert t.history == []
        with pytest.raises(ResponseParseError):
            d.source.cv_loop_speed_query()
