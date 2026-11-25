"""Source-range regressions: synthetic bounds, not instrument qualification."""
import math

import pytest
from scpi_driver_core import ConfigurationError, UnsupportedOperationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D, MethodQualification, MethodEvidence
from itech_driver.capabilities import CapabilityState
from itech_driver.command_specs import command_spec, source_bound_command, execute_source_bound

MODEL = "IT-M3902D-80-40"
CASES = [
    ("voltage", "SOUR:VOLT", 58),
    ("current", "SOUR:CURR", 39),
    ("output_power_limit", "SOUR:POW:LIM", 77),
    ("voltage_limit", "SOUR:VOLT:LIM", 76),
    ("current_limit", "SOUR:CURR:LIM", 56),
    ("programmed_power_limit", "SOUR:POW:LIM", 77),
    ("ovp_delay", "SOUR:VOLT:OVER:PROT:DEL", 68),
    ("ocp_delay", "SOUR:CURR:OVER:PROT:DEL", 48),
    ("opp_delay", "SOUR:POW:OVER:PROT:DEL", 82),
    ("uvp_delay", "SOUR:VOLT:UND:PROT:DEL", 72),
    ("ucp_delay", "SOUR:CURR:UND:PROT:DEL", 53),
    ("uvp_warmup", "SOUR:VOLT:UND:PROT:WARM", 74),
    ("ucp_warmup", "SOUR:CURR:UND:PROT:WARM", 55),
    ("voltage_rise_time", "SOUR:VOLT:SLEW:POS", 61),
    ("voltage_fall_time", "SOUR:VOLT:SLEW:NEG", 63),
    ("voltage_both_time", "SOUR:VOLT:SLEW:BOTH", 60),
    ("current_rise_time", "SOUR:CURR:SLEW:POS", 42),
    ("current_fall_time", "SOUR:CURR:SLEW:NEG", 44),
    ("current_both_time", "SOUR:CURR:SLEW:BOTH", 41),
    ("resistance", "SOUR:RES", 84),
]


def fixture(header):
    return (ScriptedScpiTransport().on("*IDN?", f"ITECH,{MODEL},S,1")
            .on("SOUR:FUNC?", "VOLT").on(header + "? MIN", "1")
            .on(header + "? MAX", "5").on(header + " 1").on(header + " 5"))


@pytest.mark.parametrize("name,header,page", CASES)
def test_documented_selector_syntax_and_boundaries(name, header, page):
    method = f"SourceSubsystem.{name}_query"
    spec = command_spec(method)
    assert spec.guide_page == page
    assert spec.bound_selectors == ("MIN", "MAX", "DEF")
    for bound in spec.bound_selectors:
        assert source_bound_command(method, bound) == f"{header}? {bound}"
    for value in (1, 5):
        t = fixture(header)
        with ITM3900D("sim", transport=t) as d:
            getattr(d.source, name + "_set")(value)
        assert t.history[-3:] == [header + "? MIN", header + "? MAX", f"{header} {value}"]


@pytest.mark.parametrize("name,header,page", CASES)
@pytest.mark.parametrize("value", [math.nextafter(1.0, -math.inf), math.nextafter(5.0, math.inf),
                                   float("nan"), float("inf"), -float("inf"), "2", True])
def test_rejected_setpoints_never_write(name, header, page, value):
    t = fixture(header)
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            getattr(d.source, name + "_set")(value)
    assert all("?" in command for command in t.history)


@pytest.mark.parametrize("name", ["ovp", "ocp", "opp_threshold", "uvp", "ucp"])
def test_threshold_does_not_allow_speculative_selector(name):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(UnsupportedOperationError):
            execute_source_bound(d, f"SourceSubsystem.{name}_query", "MIN")
    assert t.history == []


def test_invalid_resistance_selector_rejected_before_cv_query():
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            d.source.resistance_query(bound="INVALID")
    assert t.history == []


def test_discovery_rechecks_profile_after_refresh(monkeypatch):
    t = fixture("SOUR:VOLT")
    keys = ["voltage_query", "current_query", "voltage_limit_query",
            "current_limit_query", "programmed_power_limit_query"]
    with ITM3900D("sim", transport=t) as d:
        d.bind_method_qualification(MethodQualification(MODEL, "1", t.descriptor.kind,
            {f"SourceSubsystem.{key}": MethodEvidence(CapabilityState.SUPPORTED, "synthetic only")
             for key in keys}))
        original = d.identity_snapshot

        def invalidate_on_refresh(*, refresh=False):
            identity = original(refresh=refresh)
            if refresh:
                # Simulate the invalidation performed by identity_snapshot on mismatch.
                d._method_qualification = None
                d._qualification_generation = None
            return identity

        monkeypatch.setattr(d, "identity_snapshot", invalidate_on_refresh)
        with pytest.raises(UnsupportedOperationError):
            d.discover_capabilities()
    assert t.history == ["*IDN?", "*IDN?"]
