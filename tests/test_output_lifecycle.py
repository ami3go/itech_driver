import pytest
from scpi_driver_core import SafetyGuardError
from scpi_driver_core.exceptions import TransportTimeoutError
from scpi_driver_core.simulation import ScriptedScpiTransport, ScriptedReply
from itech_driver import ITM3900D
from itech_driver.output_lifecycle import request_output_off, request_output_on, observe_output


def scripted(state="0",voltage="0",current="0",questionable="0"):
    return (ScriptedScpiTransport().on("OUTP:STAT?",state)
            .on("STAT:QUES:COND?",questionable).on("MEAS:VOLT?",voltage)
            .on("MEAS:CURR?",current))


def test_off_is_not_physical_safety():
    t=scripted(voltage="5").on("OUTP:STAT OFF")
    with ITM3900D("sim",transport=t) as d:
        r=request_output_off(d,max_residual_v=0.1,max_residual_a=0.1,max_samples=2)
        assert r.outcome=="not_confirmed"
        assert t.history.count("OUTP:STAT OFF")==1
        assert t.history.count("MEAS:VOLT?")==2


def test_device_evidence_distinct_from_protection():
    t=scripted(questionable="4").on("OUTP:STAT OFF")
    with ITM3900D("sim",transport=t) as d:
        r=request_output_off(d,max_residual_v=0.1,max_residual_a=0.1)
        assert r.outcome=="instrument_below_limits"
        assert r.questionable==4


@pytest.mark.parametrize("bad",["UNKNOWN","ONWARD"])
def test_malformed_state_unknown(bad):
    with ITM3900D("sim",transport=scripted(state=bad)) as d:
        assert observe_output(d).outcome=="unknown"


def test_off_timeout_never_replayed():
    t=scripted().on("OUTP:STAT OFF",ScriptedReply(raises=TransportTimeoutError("lost")))
    with ITM3900D("sim",transport=t) as d:
        assert request_output_off(d,max_residual_v=0.1,max_residual_a=0.1).outcome=="unknown"
        assert t.history==["OUTP:STAT OFF"]


def test_enable_authorization_and_protection():
    t=scripted().on("SOUR:VOLT:OVER:PROT:STAT?","0").on("SOUR:VOLT:OVER:PROT:LEV?","10").on("SOUR:VOLT:LIM?","10")
    with ITM3900D("sim",transport=t) as d:
        with pytest.raises(SafetyGuardError):
            request_output_on(d,max_voltage_v=10,max_current_a=1,max_power_w=10)
        assert t.history==[]
        with pytest.raises(SafetyGuardError):
            request_output_on(d,authorized=True,max_voltage_v=10,max_current_a=1,max_power_w=10)
        assert "OUTP:STAT ON" not in t.history
