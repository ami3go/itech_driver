import pytest
from itech_driver import ITM3900D
from itech_driver.simulator import ItechSimulator
from itech_driver.arb_lifecycle import ArbLifecycle, ArbState
from scpi_driver_core import SafetyGuardError, ConfigurationError, TransportTimeoutError
from scpi_driver_core.simulation import ScriptedScpiTransport


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
        assert sim.transport.history.count("ABORt:ARB")==1
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
        assert "ABORt:ARB" not in sim.transport.history


def test_aliases_share_one_canonical_write():
    t = ScriptedScpiTransport().on("INITiate:ARB").on("ABORt:ARB")
    with ITM3900D("sim", transport=t) as d:
        d.arb.init()
        d.initiate.arb()
        d.arb.abort()
        d.abort.arb()
    assert t.history == ["INITiate:ARB"] * 2 + ["ABORt:ARB"] * 2


@pytest.mark.parametrize("bad", [True, 1.5, 0, -1, 1000000, "1"])
def test_arm_validates_entire_repeat_count_before_io(bad):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d, pytest.raises(ConfigurationError):
        lifecycle(d).arm(source="BUS", repeat_count=bad, configuration_confirmed=True)
    assert t.history == []


@pytest.mark.parametrize("failure", ["TRIG:ARB:SOUR BUS", "ARB:COUNT 1", "INITiate:ARB", "ARB:EXE:STAT?"])
def test_arm_failure_never_continues_or_triggers(failure):
    commands = ["TRIG:ARB:SOUR BUS", "ARB:COUNT 1", "INITiate:ARB", "ARB:EXE:STAT?"]
    t = ScriptedScpiTransport()
    for c in commands[:-1]:
        t.on(c)
    t.on(commands[-1], "ARMED")
    def fail(_):
        raise TransportTimeoutError("lost")
    t.on(failure, fail)
    with ITM3900D("sim", transport=t) as d:
        a = lifecycle(d)
        assert a.arm(source="BUS", repeat_count=1, configuration_confirmed=True).state == ArbState.UNKNOWN
        with pytest.raises(SafetyGuardError):
            a.trigger_bus()
    assert t.history == commands[:commands.index(failure)+1]


def test_trigger_readback_still_armed_cannot_replay():
    t = (ScriptedScpiTransport().on("TRIG:ARB:SOUR BUS").on("ARB:COUNT 1")
         .on("INITiate:ARB").on("ARB:EXE:STAT?", "ARMED").on("*TRG"))
    with ITM3900D("sim", transport=t) as d:
        a = lifecycle(d)
        a.arm(source="BUS", repeat_count=1, configuration_confirmed=True)
        a.trigger_bus()
        with pytest.raises(SafetyGuardError):
            a.trigger_bus()
    assert t.history.count("*TRG") == 1


@pytest.mark.parametrize("lost", [True, False])
def test_unconfirmed_abort_is_unknown_and_not_replayed(lost):
    t = (ScriptedScpiTransport().on("TRIG:ARB:SOUR EXT").on("ARB:COUNT 1")
         .on("INITiate:ARB").on("ARB:EXE:STAT?", "ARMED").on("ABORt:ARB"))
    if lost:
        def fail(_):
            raise TransportTimeoutError("lost abort")
        t.on("ABORt:ARB", fail)
    with ITM3900D("sim", transport=t) as d:
        a = lifecycle(d)
        a.arm(source="EXT", repeat_count=1, configuration_confirmed=True)
        assert a.abort().state == ArbState.UNKNOWN
        assert a.abort().state == ArbState.UNKNOWN
    assert t.history.count("ABORt:ARB") == 1
    assert "OUTP:STAT OFF" not in t.history


def test_lifecycle_trigger_timeout_no_replay():
    sim = ItechSimulator()
    def fail(_):
        raise TransportTimeoutError("lost trigger")
    sim.transport.on("*TRG", fail)
    with ITM3900D("sim", transport=sim.transport) as d:
        a = lifecycle(d)
        a.arm(source="BUS", repeat_count=1, configuration_confirmed=True)
        assert a.trigger_bus().state == ArbState.UNKNOWN
        with pytest.raises(SafetyGuardError):
            a.trigger_bus()
    assert sim.transport.history.count("*TRG") == 1
