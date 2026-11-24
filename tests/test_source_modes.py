import pytest
from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("api,header,mode,token", [
    ("function","SOUR:FUNC","voltage","VOLT"),
    ("function","SOUR:FUNC","current","CURR"),
    ("function_mode","SOUR:FUNC:MODE","fixed","FIX"),
    ("function_mode","SOUR:FUNC:MODE","list","LIST"),
    ("function_mode","SOUR:FUNC:MODE","battery","BATT"),
    ("transient_mode","SOUR:FUNC:MODE","list","LIST"),
])
def test_modes(api, header, mode, token):
    t = ScriptedScpiTransport().on(f"{header} {token}").on(f"{header}?", mode.upper())
    with ITM3900D("sim", transport=t) as d:
        getattr(d.source, api + "_set")(mode)
        assert getattr(d.source, api + "_query")() == token
        assert t.history == [f"{header} {token}", f"{header}?"]


def test_invalid_modes_and_readback():
    t = ScriptedScpiTransport().on("SOUR:FUNC:MODE?", "TRANS")
    with ITM3900D("sim", transport=t) as d:
        for mode in ("TRAN", "FIX;*RST", 1, None):
            with pytest.raises(ConfigurationError):
                d.source.function_mode_set(mode)
        with pytest.raises(ConfigurationError):
            d.source.function_set("CV")
        assert t.history == []
        with pytest.raises(ResponseParseError):
            d.source.function_mode_query()
