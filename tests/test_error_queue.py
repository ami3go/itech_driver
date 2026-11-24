import pytest
from scpi_driver_core import ConfigurationError, ScpiErrorQueueError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


def test_error_checking_is_opt_in_and_never_replays_write():
    t = ScriptedScpiTransport(error_query="SYST:SIMERR?").on("*TRG")
    replies = iter(['-113,"Undefined header"', '0,"No error"'])
    t.on("SYST:ERR?", lambda _: next(replies))
    with ITM3900D("sim", transport=t) as d:
        assert t.history == []
        d.write_scpi("*TRG")
        assert t.history == ["*TRG"]
        d.enable_scpi_error_checking()
        with pytest.raises(ScpiErrorQueueError):
            d.write_scpi("*TRG")
        assert t.history == ["*TRG", "*TRG", "SYST:ERR?", "SYST:ERR?"]
        d.disable_scpi_error_checking()
        d.write_scpi("*TRG")
        assert t.history[-1] == "*TRG"


def test_explicit_drain_and_limit():
    t = ScriptedScpiTransport(error_query="SYST:SIMERR?").on("SYST:ERR?", '-222,"Data out of range"')
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            d.drain_scpi_errors(max_entries=0)
        assert t.history == []
        with pytest.raises(ScpiErrorQueueError) as failure:
            d.drain_scpi_errors(max_entries=2)
        assert len(failure.value.errors) == 2
        assert t.history == ["SYST:ERR?", "SYST:ERR?"]


def test_malformed_queue_reply():
    t = ScriptedScpiTransport(error_query="SYST:SIMERR?").on("SYST:ERR?", "invalid")
    with ITM3900D("sim", transport=t) as d, pytest.raises(ScpiErrorQueueError):
        d.drain_scpi_errors()


def test_clean_queue():
    t = ScriptedScpiTransport(error_query="SYST:SIMERR?").on("SYST:ERR?", '0,"No error"')
    with ITM3900D("sim", transport=t) as d:
        assert d.drain_scpi_errors() == []
        assert t.history == ["SYST:ERR?"]
