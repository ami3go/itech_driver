import pytest
from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("reply,expected", [("0",False),("OFF",False),("1",True),("ON",True)])
def test_beeper_response(reply, expected):
    t = ScriptedScpiTransport().on("SYST:BEEPer:STATe?", reply)
    with ITM3900D("sim", transport=t) as d:
        assert d.system.beeper_state_query() is expected


@pytest.mark.parametrize("reply", ["ONWARD", "OFFLINE", "UNKNOWN", "2", "-1"])
@pytest.mark.parametrize("subsystem,method,command", [
    ("system","beeper_state_query","SYST:BEEPer:STATe?"),
    ("output","watchdog_query","OUTP:PROT:WDOG:STAT?"),
    ("arb","pause_query","ARB:PAUSe:STATe?"),
    ("initiate","continuous_arb_query","INITiate:CONTinuous:ARB?"),
    ("initiate","continuous_acq_query","INITiate:CONTinuous:ACQuire?"),
])
def test_invalid_boolean_never_implies_off(subsystem, method, command, reply):
    t = ScriptedScpiTransport().on(command, reply)
    with ITM3900D("sim", transport=t) as d, pytest.raises(ResponseParseError):
        getattr(getattr(d, subsystem), method)()


def test_beeper_invalid_argument_no_io():
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            d.system.beeper_state_set("OFF")
        assert t.history == []
