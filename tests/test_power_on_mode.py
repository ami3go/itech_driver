import pytest
from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("mode", ["RST", "LAST_OFF", "LAST_ON"])
def test_power_on_policy(mode):
    cmd = f"OUTP:PON:STAT {mode}"
    t = ScriptedScpiTransport().on(cmd).on("OUTP:PON:STAT?",mode)
    with ITM3900D("sim",transport=t) as d:
        d.output.power_on_mode_set(mode.lower(),allow_restore_output=mode=="LAST_ON")
        assert d.output.power_on_mode_query() == mode
        assert t.history == [cmd,"OUTP:PON:STAT?"]


def test_restore_output_needs_explicit_acknowledgment():
    t = ScriptedScpiTransport().on("OUTP:PON:STAT?","unknown")
    with ITM3900D("sim",transport=t) as d:
        for mode in ("LAST_ON","ON","LAST_OFF;*RST"):
            with pytest.raises(ConfigurationError):
                d.output.power_on_mode_set(mode)
        assert t.history == []
        with pytest.raises(ResponseParseError):
            d.output.power_on_mode_query()
