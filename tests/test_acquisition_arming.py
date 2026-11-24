import pytest
from scpi_driver_core import ConfigurationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("source", ["EXT","BUS","MAN","IMM","VOLT","CURR"])
def test_acquire_start_arms_without_software_trigger(source):
    t = ScriptedScpiTransport().on(f"TRIG:ACQ:SOUR {source}").on("INIT:ACQ")
    with ITM3900D("sim", transport=t) as d:
        d.trigger.acquire_start(source)
        assert t.history == [f"TRIG:ACQ:SOUR {source}", "INIT:ACQ"]


def test_immediate_trigger_is_explicit():
    t = ScriptedScpiTransport().on("TRIG:ACQuire:IMMediate")
    with ITM3900D("sim", transport=t) as d:
        d.trigger.acquire_immediate()
        assert t.history == ["TRIG:ACQuire:IMMediate"]


def test_invalid_source_never_arms():
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            d.trigger.acquire_start("invalid")
        assert t.history == []
