import pytest
from scpi_driver_core import ConfigurationError, ResponseParseError, UnsupportedOperationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("api,header", [("acquire", "ACQ"), ("arb", "ARB"), ("dlog", "DLOG"), ("elog", "ELOG")])
@pytest.mark.parametrize("value,token", [("external","EXT"), ("BUS","BUS"), ("manual","MAN"), ("immediate","IMM")])
def test_common_sources(api, header, value, token):
    t = ScriptedScpiTransport().on(f"TRIG:{header}:SOUR {token}").on(f"TRIG:{header}:SOUR?", value)
    with ITM3900D("sim", transport=t) as d:
        getattr(d.trigger, api + "_source_set")(value)
        assert getattr(d.trigger, api + "_source_query")() == token
        assert t.history == [f"TRIG:{header}:SOUR {token}", f"TRIG:{header}:SOUR?"]


@pytest.mark.parametrize("api,header", [("acquire","ACQ"),("dlog","DLOG"),("elog","ELOG")])
@pytest.mark.parametrize("source", ["VOLT","CURR"])
def test_quantity_sources(api, header, source):
    t = ScriptedScpiTransport().on(f"TRIG:{header}:SOUR {source}")
    with ITM3900D("sim", transport=t) as d:
        getattr(d.trigger, api + "_source_set")(source)
        assert t.history == [f"TRIG:{header}:SOUR {source}"]


def test_invalid_and_ambiguous_sources_do_not_write():
    t = ScriptedScpiTransport().on("TRIG:ARB:SOUR?", "VOLT")
    with ITM3900D("sim", transport=t) as d:
        for source in ("VOLT", "CURR", "EXT;*RST", None):
            with pytest.raises(ConfigurationError):
                d.trigger.arb_source_set(source)
        with pytest.raises(UnsupportedOperationError):
            d.trigger.source_set("EXT")
        with pytest.raises(UnsupportedOperationError):
            d.trigger.source_query()
        assert t.history == []
        with pytest.raises(ResponseParseError):
            d.trigger.arb_source_query()
