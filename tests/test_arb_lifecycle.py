import pytest
from itech_driver import ITM3900D
from itech_driver.simulator import ItechSimulator
from itech_driver.arb_lifecycle import ArbLifecycle, ArbState
from scpi_driver_core import SafetyGuardError


MAP={s.name:s for s in ArbState}


def lifecycle(driver):
    return ArbLifecycle(driver,status_map=MAP,mapping_evidence="synthetic fixture only")


def test_bus_sequence_and_complete():
    sim=ItechSimulator()
    with ITM3900D("sim",transport=sim.transport) as d:
        a=lifecycle(d)
        assert a.arm(source="BUS",repeat_count=2,configuration_confirmed=True).state==ArbState.ARMED
        assert a.trigger_bus().state==ArbState.RUNNING
        assert a.wait(max_polls=4,between_polls=sim.tick).state==ArbState.COMPLETE
        assert sim.transport.history.count("*TRG")==1


def test_external_trigger_not_sent_early():
    sim=ItechSimulator()
    with ITM3900D("sim",transport=sim.transport) as d:
        a=lifecycle(d)
        a.arm(source="EXT",repeat_count=1,configuration_confirmed=True)
        with pytest.raises(SafetyGuardError):
            a.trigger_bus()
        assert "*TRG" not in sim.transport.history
        sim.external_trigger()
        sim.tick()
        assert a.wait(max_polls=1).state==ArbState.COMPLETE


def test_timeout_budget_and_cancel():
    sim=ItechSimulator()
    with ITM3900D("sim",transport=sim.transport) as d:
        a=lifecycle(d)
        a.arm(source="EXT",repeat_count=1,configuration_confirmed=True)
        assert a.wait(max_polls=2).state==ArbState.UNKNOWN
        assert a.wait(max_polls=2,cancelled=lambda:True).state==ArbState.ABORTED
        assert sim.transport.history.count("ABOR:ARB")==1
        assert "OUTP:STAT OFF" not in sim.transport.history


def test_reconnect_invalidates_ownership():
    sim=ItechSimulator()
    with ITM3900D("sim",transport=sim.transport) as d:
        a=lifecycle(d)
        a.arm(source="BUS",repeat_count=1,configuration_confirmed=True)
        d.close()
        d.session.open()
        assert a.observe().state==ArbState.UNKNOWN
        with pytest.raises(SafetyGuardError):
            a.trigger_bus()
        assert a.abort().state==ArbState.UNKNOWN
        assert "ABOR:ARB" not in sim.transport.history
