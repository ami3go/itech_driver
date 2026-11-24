from dataclasses import FrozenInstanceError
import pytest
from scpi_driver_core import ConfigurationError, UnsupportedOperationError, IdentityError
from scpi_driver_core.scpi.parsers import parse_identity
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import GenericSCPIInstrument, ITM3900D
from itech_driver.capabilities import (ApplicationLimits, CapabilityState, ElectricalRanges,
    MODEL_DESCRIPTORS, Range, RATINGS, descriptor_for, effective_ranges)
from itech_driver.identity import is_itm3900d
from itech_driver.config import Config


def test_normalized_identity_and_unknown_firmware_not_feature_support():
    ident = parse_identity('itech, it-m3902d-80-40 ,SN,UNKNOWN')
    assert is_itm3900d(ident)
    desc = descriptor_for(ident)
    assert desc.ratings == RATINGS["IT-M3902D-80-40"]
    assert desc.channels == 1
    assert desc.state("identity") is CapabilityState.SUPPORTED
    assert desc.state("output_control") is CapabilityState.UNQUALIFIED
    assert desc.state("not_in_registry") is CapabilityState.UNKNOWN
    with pytest.raises(UnsupportedOperationError):
        desc.require("output_control")
    with pytest.raises(TypeError):
        desc.features["output_control"] = CapabilityState.SUPPORTED
    with pytest.raises(TypeError):
        RATINGS["new"] = desc.ratings
    with pytest.raises(FrozenInstanceError):
        desc.channels = 2


def test_unknown_descriptor_never_invents_ratings():
    assert descriptor_for(parse_identity("OTHER,IT-M3902D-80-40,S,1")) is None
    assert descriptor_for(parse_identity("ITECH,IT-M3900D,S,1")) is None


def test_generic_explicit_states_without_io():
    t = ScriptedScpiTransport()
    with GenericSCPIInstrument("sim", transport=t) as d:
        assert set(d.capability_states().values()) == {CapabilityState.UNKNOWN}
        assert all(x is None for x in d.detect_capabilities().values())
        assert t.history == []


@pytest.mark.parametrize("model,expected_v,expected_a,expected_w", [
    ("IT-M3902D-80-40", 80, 40, 2000),
    ("IT-M3906D-1500-12", 1500, 12, 6000),
])
def test_nominal_live_and_application_limits(model, expected_v, expected_a, expected_w):
    desc = MODEL_DESCRIPTORS[model]
    live = ElectricalRanges(*(Range(0, 9999) for _ in range(5)))
    e = effective_ranges(desc, live)
    assert (e.voltage.maximum, e.current.maximum, e.power_limit.maximum) == (expected_v, expected_a, expected_w)
    app = ApplicationLimits(Range(2, 10), Range(0, 5), Range(0, 25))
    e = effective_ranges(desc, live, app)
    assert e.voltage == Range(2, 10)
    assert e.current_limit == Range(0, 5)
    assert e.power_limit == Range(0, 25)


def test_unknown_and_disjoint_ranges_fail_closed():
    live = ElectricalRanges(*(Range(0, 10) for _ in range(5)))
    with pytest.raises(ConfigurationError):
        effective_ranges(None, live)
    with pytest.raises(ConfigurationError):
        effective_ranges(MODEL_DESCRIPTORS["IT-M3902D-80-40"], None)
    with pytest.raises(ConfigurationError):
        effective_ranges(MODEL_DESCRIPTORS["IT-M3902D-80-40"], live, ApplicationLimits(voltage=Range(20, 30)))


@pytest.mark.parametrize("lo,hi", [(float("nan"), 1), (0, float("inf")), (True, 1), (2, 1)])
def test_invalid_ranges(lo, hi):
    with pytest.raises(ConfigurationError):
        Range(lo, hi)


def test_config_application_limits_are_not_hardware_ratings(tmp_path):
    c = Config(tmp_path / "app.json", allow_missing=True)
    assert ApplicationLimits.from_config(c) == ApplicationLimits()
    c.set("default_voltage_range", (2, 20))
    c.set("safe_limits", {"max_voltage": 10, "max_power": 40})
    assert ApplicationLimits.from_config(c) == ApplicationLimits(Range(2, 10), None, Range(0, 40))


def test_discovery_preserves_reported_range_and_applies_application_limits():
    t = ScriptedScpiTransport().on("*IDN?", "ITECH,IT-M3902D-80-40,S,1")
    for h in ("SOUR:VOLT", "SOUR:CURR", "SOUR:VOLT:LIM", "SOUR:CURR:LIM", "SOUR:POW:LIM"):
        t.on(h + "? MIN", "0").on(h + "? MAX", "100")
    with ITM3900D("sim", transport=t) as d:
        c = d.discover_capabilities(application_limits=ApplicationLimits(voltage=Range(0, 12)))
        assert c.live_ranges.voltage == Range(0, 100)
        assert c.voltage == Range(0, 12)
        assert c.ratings.voltage_v == 80
    assert all("?" in cmd for cmd in t.history)
