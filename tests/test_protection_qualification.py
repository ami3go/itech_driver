import pytest
from scpi_driver_core import ConfigurationError, UnsupportedOperationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D
from itech_driver.capabilities import ApplicationLimits, Range
from itech_driver.protection import ProtectionThresholdQualification, PROTECTION_THRESHOLDS


MODEL = "IT-M3902D-80-40"
METHODS = [("ovp", "ovp_set"), ("ocp", "ocp_set"), ("opp", "opp_threshold_set"),
           ("uvp", "uvp_set"), ("ucp", "ucp_set")]


def qualification(kind, firmware="1", model=MODEL):
    return ProtectionThresholdQualification(model, firmware, kind, Range(1, 5), "synthetic fixture only")


@pytest.mark.parametrize("kind,method", METHODS)
def test_threshold_requires_qualification_and_valid_bounds_before_io(kind, method):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(UnsupportedOperationError):
            getattr(d.source, method)(2)
        for bad in (0, 6, True, "2", float("nan"), float("inf")):
            with pytest.raises(ConfigurationError):
                getattr(d.source, method)(bad, qualification=qualification(kind))
    assert t.history == []


@pytest.mark.parametrize("kind,method", METHODS)
def test_command_specific_boundary_no_speculative_queries(kind, method):
    header = PROTECTION_THRESHOLDS[kind][0]
    t = ScriptedScpiTransport().on("*IDN?", f"ITECH,{MODEL},SIM,1").on(header+" 1").on(header+" 5")
    with ITM3900D("sim", transport=t) as d:
        for v in (1, 5):
            getattr(d.source, method)(v, qualification=qualification(kind))
    assert t.history == ["*IDN?", header+" 1", header+" 5"]


@pytest.mark.parametrize("idn", [
    "ITECH,IT-M3906D-1500-12,S,1", "ITECH,IT-M3902D-80-40,S,2", "OTHER,IT-M3902D-80-40,S,1"
])
def test_evidence_bound_to_exact_identity(idn):
    t = ScriptedScpiTransport().on("*IDN?", idn)
    with ITM3900D("sim", transport=t) as d, pytest.raises(UnsupportedOperationError):
        d.source.ovp_set(2, qualification=qualification("ovp"))
    assert t.history == ["*IDN?"]


def test_application_ceiling_not_nominal_protection_range():
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t, application_limits=ApplicationLimits(voltage=Range(3, 4))) as d:
        with pytest.raises(ConfigurationError):
            d.source.ovp_set(5, qualification=qualification("ovp"))
        with pytest.raises(UnsupportedOperationError):
            d.source.ovp_set(3, qualification=qualification("ocp"))
    assert t.history == []
