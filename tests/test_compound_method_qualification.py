import pytest
from scpi_driver_core import UnsupportedOperationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D, MethodQualification, MethodEvidence, ArbIntegerQualification, ArbIntegerBounds
from itech_driver.capabilities import CapabilityState
from itech_driver.acquisition import AcquisitionConfig, configure_and_arm
from itech_driver.arb_lifecycle import ArbLifecycle, ArbState
from itech_driver.output_lifecycle import request_output_on, request_output_off
from itech_driver.command_specs import execute

MODEL = "IT-M3902D-80-40"


def make():
    return ScriptedScpiTransport().on("*IDN?", f"ITECH,{MODEL},S,1")


def bind(d, t, keys):
    d.bind_method_qualification(MethodQualification(MODEL, "1", t.descriptor.kind,
        {k: MethodEvidence(CapabilityState.SUPPORTED, "synthetic only") for k in keys}))


def test_acquisition_preflights_all_methods_before_first_write():
    t = make()
    with ITM3900D("sim", transport=t) as d:
        bind(d,t,["SenseSubsystem.acquisition_points_set"])
        with pytest.raises(UnsupportedOperationError):
            configure_and_arm(d, AcquisitionConfig(10, 0, 0.01, "BUS"))
    assert t.history == ["*IDN?"]


def test_arb_preflights_arm_before_first_write():
    t = make()
    with ITM3900D("sim", transport=t) as d:
        bind(d,t,["TriggerSubsystem.arb_source_set", "ArbSubsystem.count_set"])
        d.bind_arb_integer_qualification(ArbIntegerQualification(MODEL, "1",
            {"count_set": ArbIntegerBounds(1, 10, "synthetic only")}))
        a = ArbLifecycle(d,status_map={"ARMED":ArbState.ARMED},mapping_evidence="synthetic only")
        with pytest.raises(UnsupportedOperationError):
            a.arm(source="BUS",repeat_count=2,configuration_confirmed=True)
    assert t.history == ["*IDN?", "*IDN?"]


def test_output_on_missing_qualification_never_probes_or_writes():
    t = make()
    with ITM3900D("sim", transport=t) as d:
        bind(d,t,["OutputSubsystem.state_query","OutputSubsystem.state_set"])
        with pytest.raises(UnsupportedOperationError):
            request_output_on(d, authorized=True, max_voltage_v=5, max_current_a=1,max_power_w=5)
    assert t.history == ["*IDN?"]


def test_qualified_off_not_blocked_by_missing_observation():
    t = make().on("OUTP:STAT OFF")
    with ITM3900D("sim", transport=t) as d:
        bind(d,t,["OutputSubsystem.state_set"])
        e = request_output_off(d,max_residual_v=0.1,max_residual_a=0.1)
        assert e.outcome == "unknown"
    assert t.history == ["*IDN?", "OUTP:STAT OFF"]


def test_registry_executor_cannot_bypass_typed_guard():
    t = make()
    with ITM3900D("sim", transport=t, require_qualified_capabilities=True) as d:
        with pytest.raises(UnsupportedOperationError):
            execute(d,"OutputSubsystem.state_set",True)
    assert t.history == []
