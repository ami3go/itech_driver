import pytest
from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("name,header", [["oper_positive_transition","STAT:OPER:PTR"],["oper_negative_transition","STAT:OPER:NTR"],["ques_positive_transition","STAT:QUES:PTR"],["ques_negative_transition","STAT:QUES:NTR"]])
@pytest.mark.parametrize("mask", [0,65535])
def test_transition_mask(name,header,mask):
    t = ScriptedScpiTransport().on(f"{header} {mask}").on(header+"?",str(mask))
    with ITM3900D("sim",transport=t) as d:
        getattr(d.status,name+"_set")(mask)
        assert getattr(d.status,name+"_query")() == mask
        assert t.history == [f"{header} {mask}",header+"?"]


@pytest.mark.parametrize("mask", [-1,65536,True,1.5])
def test_invalid_mask(mask):
    t = ScriptedScpiTransport()
    with ITM3900D("sim",transport=t) as d:
        with pytest.raises(ConfigurationError):
            d.status.oper_positive_transition_set(mask)
        assert t.history == []


def test_event_read_is_destructive_in_simulator_and_not_replayed():
    replies = iter(["4","0"])
    t = ScriptedScpiTransport().on("STAT:QUES:EVEN?", lambda _: next(replies))
    with ITM3900D("sim",transport=t) as d:
        assert d.status.ques_event_query() == 4
        assert d.status.ques_event_query() == 0
        assert t.history == ["STAT:QUES:EVEN?","STAT:QUES:EVEN?"]


def test_bad_mask_response():
    t = ScriptedScpiTransport().on("STAT:OPER:PTR?","65536")
    with ITM3900D("sim",transport=t) as d, pytest.raises(ResponseParseError):
        d.status.oper_positive_transition_query()
