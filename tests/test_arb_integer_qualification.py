import pytest
from scpi_driver_core import ConfigurationError, UnsupportedOperationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D, ArbIntegerBounds, ArbIntegerQualification, MethodQualification, MethodEvidence
from itech_driver.capabilities import CapabilityState
from itech_driver.arb_lifecycle import ArbLifecycle, ArbState

MODEL = "IT-M3902D-80-40"
def qualification(method, model=MODEL, firmware="1"):
    return ArbIntegerQualification(model, firmware, {method: ArbIntegerBounds(2, 4, "synthetic test only")})


@pytest.mark.parametrize("method,args,wire", [
    ("udef_count_set", (), "ARB:UDEFined:COUNt 4"),
    ("udef_level_set", (2,), "ARB:UDEFined:LEVel 4,2.0"),
    ("udef_dwell_set", (1,), "ARB:UDEFined:DWELl 4,1.0"),
    ("udef_slew_set", (1,), "ARB:UDEFined:SLEW 4,1.0"),
    ("count_set", (), "ARB:COUNT 4"), ("save", (), "ARB:SAVE 4"), ("recall", (), "ARB:RECall 4"),
])
def test_exact_model_command_bounds(method, args, wire):
    t = ScriptedScpiTransport().on("*IDN?", f"ITECH,{MODEL},S,1").on(wire)
    with ITM3900D("sim", transport=t) as d:
        d.bind_arb_integer_qualification(qualification(method))
        for value in (1, 5, True, 2.5):
            with pytest.raises(ConfigurationError):
                getattr(d.arb, method)(value, *args)
        getattr(d.arb, method)(4, *args)
    assert t.history == ["*IDN?", wire]


def test_wrong_command_cannot_use_another_bound():
    t = ScriptedScpiTransport().on("*IDN?", f"ITECH,{MODEL},S,1")
    with ITM3900D("sim", transport=t) as d:
        d.bind_arb_integer_qualification(qualification("save"))
        with pytest.raises(UnsupportedOperationError):
            d.arb.recall(2)
    assert t.history == ["*IDN?"]


@pytest.mark.parametrize("reply", ["ITECH,IT-M3906D-1500-12,S,1", f"ITECH,{MODEL},S,2"])
def test_wrong_identity_fails_closed(reply):
    t = ScriptedScpiTransport().on("*IDN?", reply)
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(UnsupportedOperationError):
            d.bind_arb_integer_qualification(qualification("count_set"))
        with pytest.raises(UnsupportedOperationError):
            d.arb.count_set(2)
    assert t.history == ["*IDN?"]


def test_reconnect_and_arm_fail_before_configuration():
    t = ScriptedScpiTransport().on("*IDN?", f"ITECH,{MODEL},S,1")
    with ITM3900D("sim", transport=t) as d:
        d.bind_arb_integer_qualification(qualification("count_set"))
        lifecycle = ArbLifecycle(d, status_map={"ARMED": ArbState.ARMED}, mapping_evidence="synthetic")
        with pytest.raises(ConfigurationError):
            lifecycle.arm(source="BUS", repeat_count=5, configuration_confirmed=True)
        d.session.close()
        d.session.open()
        with pytest.raises(UnsupportedOperationError):
            lifecycle.arm(source="BUS", repeat_count=2, configuration_confirmed=True)
    assert t.history == ["*IDN?"]


def test_strict_method_evidence_does_not_establish_integer_bounds():
    t = ScriptedScpiTransport().on("*IDN?", f"ITECH,{MODEL},S,1")
    with ITM3900D("sim", transport=t, require_qualified_capabilities=True) as d:
        d.bind_method_qualification(MethodQualification(MODEL, "1", t.descriptor.kind,
            {"ArbSubsystem.count_set": MethodEvidence(CapabilityState.SUPPORTED, "synthetic")}))
        with pytest.raises(UnsupportedOperationError):
            d.arb.count_set(2)
    assert t.history == ["*IDN?"]


def test_no_qualification_can_expand_family_bounds():
    with pytest.raises(ConfigurationError):
        ArbIntegerQualification(MODEL, "1", {"save": ArbIntegerBounds(1, 11, "synthetic")})


def test_invalid_initial_binding_is_fail_closed():
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            d.bind_arb_integer_qualification(None)
        with pytest.raises(UnsupportedOperationError):
            d.arb.count_set(2)
    assert t.history == []
