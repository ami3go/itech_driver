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


def test_generic_base_retains_direct_subsystem_compatibility():
    from itech_driver import BaseInstrument
    from itech_driver.subsystems.MeasurementSubsystem import MeasurementSubsystem
    t = ScriptedScpiTransport().on("MEAS:VOLT?", "1.25")
    with BaseInstrument("sim", transport=t) as base:
        assert MeasurementSubsystem(base).voltage_query() == 1.25
    assert t.history == ["MEAS:VOLT?"]


@pytest.mark.parametrize("name", ["voltage_set","current_set","output_power_limit_set","voltage_limit_set","current_limit_set","programmed_power_limit_set","ovp_delay_set","ocp_delay_set","opp_delay_set","uvp_delay_set","ucp_delay_set","uvp_warmup_set","ucp_warmup_set","voltage_rise_time_set","voltage_fall_time_set","voltage_both_time_set","current_rise_time_set","current_fall_time_set","current_both_time_set","resistance_set"])
def test_range_setter_needs_qualified_read_before_any_probe(name):
    t = make()
    with ITM3900D("sim", transport=t) as d:
        bind(d, t, ["SourceSubsystem." + name])
        with pytest.raises(UnsupportedOperationError):
            getattr(d.source, name)(1)
    assert t.history == ["*IDN?"]


def test_qualified_range_setter_keeps_exact_wire_and_validation():
    t = make().on("SOUR:VOLT? MIN", "0").on("SOUR:VOLT? MAX", "80").on("SOUR:VOLT 5")
    with ITM3900D("sim", transport=t) as d:
        bind(d, t, ["SourceSubsystem.voltage_set", "SourceSubsystem.voltage_query"])
        d.source.voltage_set(5)
    assert t.history == ["*IDN?", "SOUR:VOLT? MIN", "SOUR:VOLT? MAX", "SOUR:VOLT 5"]


def test_discovery_does_not_probe_unqualified_ranges():
    t = make()
    with ITM3900D("sim", transport=t) as d:
        bind(d, t, ["SourceSubsystem.voltage_query"])
        with pytest.raises(UnsupportedOperationError):
            d.discover_capabilities()
    assert t.history == ["*IDN?"]
