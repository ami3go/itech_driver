import pytest
from scpi_driver_core import ConfigurationError, UnsupportedOperationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D, MethodQualification, MethodEvidence, auto_detect_instrument
from itech_driver.capabilities import CapabilityState

MODEL = "IT-M3902D-80-40"
METHOD = "MeasurementSubsystem.voltage_query"


def profile(t, model=MODEL, firmware="1", methods=None):
    return MethodQualification(model, firmware, t.descriptor.kind, methods or {
        METHOD: MethodEvidence(CapabilityState.SUPPORTED, "synthetic test only")})


def test_strict_mode_unbound_rejects_without_io():
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t, require_qualified_capabilities=True) as d:
        for call in (d.measurement.voltage_query, d.output.state_query, d.arb.state_query,
                     d.system.version, d.elog.state_query, d.ieee.self_test):
            with pytest.raises(UnsupportedOperationError):
                call()
    assert t.history == []


@pytest.mark.parametrize("model", [MODEL, "IT-M3906D-1500-12"])
def test_exact_binding_and_distinct_states(model):
    t = ScriptedScpiTransport().on("*IDN?", f"ITECH,{model},S,1").on("MEAS:VOLT?", "2.5")
    evidence = {
        METHOD: MethodEvidence(CapabilityState.SUPPORTED, "synthetic test only"),
        "OutputSubsystem.state_set": MethodEvidence(CapabilityState.UNSUPPORTED, "synthetic absent"),
        "ArbSubsystem.state_query": MethodEvidence(CapabilityState.UNQUALIFIED, "pending evidence"),
    }
    p = profile(t, model, methods=evidence)
    evidence.clear()
    with ITM3900D("sim", transport=t, require_qualified_capabilities=True) as d:
        d.bind_method_qualification(p)
        assert d.measurement.voltage_query() == 2.5
        for call, reason in ((lambda: d.output.state_set(True), "unsupported"),
                             (d.arb.state_query, "unqualified"),
                             (d.fetch.voltage_query, "unknown")):
            with pytest.raises(UnsupportedOperationError, match=reason):
                call()
    assert t.history == ["*IDN?", "MEAS:VOLT?"]


@pytest.mark.parametrize("reply", ["ITECH,IT-M3902D-80-40,S,2", "OTHER,IT-M3902D-80-40,S,1", "ITECH,UNKNOWN,S,1"])
def test_failed_bind_stays_closed(reply):
    t = ScriptedScpiTransport().on("*IDN?", reply)
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(UnsupportedOperationError):
            d.bind_method_qualification(profile(t))
        with pytest.raises(UnsupportedOperationError):
            d.measurement.voltage_query()
    assert t.history == ["*IDN?"]


def test_generation_change_requires_new_binding():
    t = ScriptedScpiTransport().on("*IDN?", f"ITECH,{MODEL},S,1")
    with ITM3900D("sim", transport=t) as d:
        d.bind_method_qualification(profile(t))
        d.session.close()
        d.session.open()
        with pytest.raises(UnsupportedOperationError):
            d.measurement.voltage_query()
    assert t.history == ["*IDN?"]


def test_quarantined_command_cannot_be_promoted():
    t = ScriptedScpiTransport()
    with pytest.raises(ConfigurationError):
        profile(t, methods={"ArbSubsystem.terminate_last_set": MethodEvidence(CapabilityState.SUPPORTED, "synthetic")})


def test_auto_detection_does_not_discard_strict_policy():
    t = ScriptedScpiTransport().on("*IDN?", "OTHER,UNKNOWN,S,1")
    from scpi_driver_core import IdentityError
    with pytest.raises(IdentityError):
        auto_detect_instrument("sim", transport=t, require_qualified_capabilities=True)
    assert not t.is_open


def test_direct_subsystem_construction_cannot_bypass_strict_guard():
    from itech_driver import SourceSubsystem, ArbSubsystem, OutputSubsystem
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t, require_qualified_capabilities=True) as d:
        for call in (lambda: SourceSubsystem(d).voltage_set(1),
                     lambda: ArbSubsystem(d).count_set(1),
                     OutputSubsystem(d).state_query):
            with pytest.raises(UnsupportedOperationError):
                call()
    assert t.history == []


def test_direct_supported_method_preserves_signature_and_wire():
    import inspect
    from itech_driver.subsystems.MeasurementSubsystem import MeasurementSubsystem
    t = ScriptedScpiTransport().on("*IDN?", f"ITECH,{MODEL},S,1").on("MEAS:VOLT?", "2.5")
    with ITM3900D("sim", transport=t) as d:
        d.bind_method_qualification(profile(t))
        direct = MeasurementSubsystem(d)
        assert inspect.signature(direct.voltage_query) == inspect.signature(d.measurement.voltage_query)
        assert direct.voltage_query() == 2.5
    assert t.history == ["*IDN?", "MEAS:VOLT?"]


@pytest.mark.parametrize("key", [
    "BatterySubsystem.state_set", "SenseSubsystem.acquisition_points_query",
    "LoggingSubsystem.DLOG.raw_data_query", "TriggerSubsystem.delay_set",
])
def test_additional_unimplemented_methods_cannot_be_promoted(key):
    t = ScriptedScpiTransport()
    with pytest.raises(ConfigurationError):
        profile(t, methods={key: MethodEvidence(CapabilityState.SUPPORTED, "synthetic")})
