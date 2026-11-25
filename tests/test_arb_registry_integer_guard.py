"""Registry entry points must not bypass ARB integer bounds."""
import pytest
from scpi_driver_core import ConfigurationError, UnsupportedOperationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D, ArbIntegerBounds, ArbIntegerQualification
from itech_driver import MethodEvidence, MethodQualification
from itech_driver.capabilities import CapabilityState
from itech_driver.command_specs import execute_parameterized
from itech_driver.arb_integer_qualification import FAMILY_INTEGER_MAX

MODEL = "IT-M3902D-80-40"
CASES = [
    ("udef_count_set", ()),
    ("udef_level_set", (2.0,)),
    ("udef_level_query", ()),
    ("udef_dwell_set", (1.0,)),
    ("udef_dwell_query", ()),
    ("udef_slew_set", (1.0,)),
    ("udef_slew_query", ()),
    ("count_set", ()),
    ("save", ()),
    ("recall", ()),
]


@pytest.mark.parametrize("operation,args", CASES)
def test_registry_rejects_invalid_family_integer(operation, args):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        for bad in (0, -1, True, 1.5, FAMILY_INTEGER_MAX[operation] + 1, 10**100):
            with pytest.raises(ConfigurationError):
                execute_parameterized(d, "ArbSubsystem." + operation, bad, *args)
    assert t.history == []


@pytest.mark.parametrize("operation,args", CASES)
def test_registry_rejects_outside_bound_profile(operation, args):
    t = ScriptedScpiTransport().on("*IDN?", f"ITECH,{MODEL},S,1")
    with ITM3900D("sim", transport=t) as d:
        d.bind_arb_integer_qualification(ArbIntegerQualification(MODEL, "1",
            {operation: ArbIntegerBounds(2, 4, "synthetic only")}))
        for bad in (1, 5):
            with pytest.raises(ConfigurationError):
                execute_parameterized(d, "ArbSubsystem." + operation, bad, *args)
    assert t.history == ["*IDN?"]


def test_registry_cannot_bypass_required_integer_profile():
    t = ScriptedScpiTransport().on("*IDN?", f"ITECH,{MODEL},S,1")
    with ITM3900D("sim", transport=t) as d:
        d.bind_method_qualification(MethodQualification(MODEL, "1", t.descriptor.kind,
            {"ArbSubsystem.count_set": MethodEvidence(CapabilityState.SUPPORTED, "synthetic only")}))
        with pytest.raises(UnsupportedOperationError):
            execute_parameterized(d, "ArbSubsystem.count_set", 2)
    assert t.history == ["*IDN?"]


def test_registry_bound_profile_valid_and_stale_generation():
    t = ScriptedScpiTransport().on("*IDN?", f"ITECH,{MODEL},S,1").on("ARB:COUNT 2")
    with ITM3900D("sim", transport=t) as d:
        d.bind_arb_integer_qualification(ArbIntegerQualification(MODEL, "1",
            {"count_set": ArbIntegerBounds(2, 4, "synthetic only")}))
        execute_parameterized(d, "ArbSubsystem.count_set", 2)
        d.session.close()
        d.session.open()
        with pytest.raises(UnsupportedOperationError):
            execute_parameterized(d, "ArbSubsystem.count_set", 2)
    assert t.history == ["*IDN?", "ARB:COUNT 2"]
