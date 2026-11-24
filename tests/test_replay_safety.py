import pytest
from scpi_driver_core.exceptions import TransportTimeoutError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D
from itech_driver.exceptions import TimeoutError


@pytest.mark.parametrize("command", ["OUTP:STAT ON", "OUTP:STAT OFF", "*RST", "*RCL 1", "INIT:ARB", "*TRG"])
def test_ambiguous_write_is_never_replayed(command):
    def lost_ack(_):
        raise TransportTimeoutError("transmitted but completion unknown")

    t = ScriptedScpiTransport(error_query="SYST:SIMERR?").on(command, lost_ack)
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(TimeoutError):
            d.write_scpi(command)
        assert t.history == [command]
        assert not d.session.is_connected


@pytest.mark.parametrize("command", ["*ESR?", "STAT:OPER:EVEN?", "STAT:QUES:EVEN?", "SYST:ERR?", "*IDN?"])
def test_lost_query_reply_is_never_replayed(command):
    def lost_reply(_):
        raise TransportTimeoutError("query reached instrument but response lost")

    t = ScriptedScpiTransport(error_query="SYST:SIMERR?").on(command, lost_reply)
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(TimeoutError):
            d.query_scpi(command)
        assert t.history == [command]
        assert not d.session.is_connected
