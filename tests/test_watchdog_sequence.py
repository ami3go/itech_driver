import pytest
from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


def test_configure_readback_before_enable():
    t = ScriptedScpiTransport().on("OUTP:PROT:WDOG:DEL 60").on("OUTP:PROT:WDOG:DEL?", "6.0E1").on("OUTP:PROT:WDOG:STAT 1")
    with ITM3900D("sim", transport=t) as d:
        d.output.watchdog_set(True, 60)
        assert t.history == ["OUTP:PROT:WDOG:DEL 60","OUTP:PROT:WDOG:DEL?","OUTP:PROT:WDOG:STAT 1"]


def test_mismatched_delay_prevents_enable():
    t = ScriptedScpiTransport().on("OUTP:PROT:WDOG:DEL 60").on("OUTP:PROT:WDOG:DEL?", "30")
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ResponseParseError):
            d.output.watchdog_set(True, 60)
        assert t.history == ["OUTP:PROT:WDOG:DEL 60","OUTP:PROT:WDOG:DEL?"]


@pytest.mark.parametrize("delay", [0,3601,1.5,True,float("nan")])
def test_invalid_delay_no_io(delay):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            d.output.watchdog_set(True, delay)
        assert t.history == []


def test_existing_delay_must_be_valid_before_enable():
    t = ScriptedScpiTransport().on("OUTP:PROT:WDOG:DEL?", "0")
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ResponseParseError):
            d.output.watchdog_set(True)
        assert t.history == ["OUTP:PROT:WDOG:DEL?"]


def test_disable_precedes_optional_delay_change():
    t = ScriptedScpiTransport().on("OUTP:PROT:WDOG:STAT 0").on("OUTP:PROT:WDOG:DEL 5").on("OUTP:PROT:WDOG:DEL?", "5")
    with ITM3900D("sim", transport=t) as d:
        d.output.watchdog_set(False, 5)
        assert t.history == ["OUTP:PROT:WDOG:STAT 0","OUTP:PROT:WDOG:DEL 5","OUTP:PROT:WDOG:DEL?"]
