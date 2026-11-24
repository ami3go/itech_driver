import pytest
from scpi_driver_core import ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


def test_arb_execution_status_raw_response():
    t = ScriptedScpiTransport().on("ARB:EXE:STAT?", "0")
    with ITM3900D("sim", transport=t) as d:
        assert d.arb.state_query() == "0"
        assert t.history == ["ARB:EXE:STAT?"]


def test_empty_status_is_not_a_completion_result():
    t = ScriptedScpiTransport().on("ARB:EXE:STAT?", "\n")
    with ITM3900D("sim", transport=t) as d, pytest.raises(ResponseParseError):
        d.arb.state_query()
