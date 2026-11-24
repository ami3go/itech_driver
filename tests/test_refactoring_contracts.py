import pytest
from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("value", ["off", object()])
def test_output_enable_rejects_ambiguous_objects(value):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            d.output.state_set(value)
    assert t.history == []


def test_empty_boolean_reply_is_invalid():
    t = ScriptedScpiTransport().on("SYST:BEEPer:STATe?", "")
    with ITM3900D("sim", transport=t) as d, pytest.raises(ResponseParseError):
        d.system.beeper_state_query()


@pytest.mark.parametrize("method", ["function_mode_set", "transient_mode_set"])
def test_aliases_reject_invalid_mode_before_io(method):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            getattr(d.source, method)("FIX;*RST")
    assert t.history == []


def test_source_mode_alias_parity():
    t = ScriptedScpiTransport().on("SOUR:FUNC:MODE FIX").on("SOUR:FUNC:MODE?", "FIX")
    with ITM3900D("sim", transport=t) as d:
        for api in ("function_mode", "transient_mode"):
            getattr(d.source, api + "_set")("FIX")
            assert getattr(d.source, api + "_query")() == "FIX"
    assert t.history == ["SOUR:FUNC:MODE FIX", "SOUR:FUNC:MODE?"] * 2
