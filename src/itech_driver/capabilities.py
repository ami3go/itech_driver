"""Rated single-unit envelopes; not firmware qualification or parallel ratings."""
from dataclasses import dataclass
from enum import Enum
import math
from types import MappingProxyType
from typing import Mapping
from scpi_driver_core import ConfigurationError, IdentityError, ResponseParseError, UnsupportedOperationError
from scpi_driver_core.scpi.parsers import parse_float


@dataclass(frozen=True)
class Ratings:
    voltage_v: float
    current_a: float
    power_w: float


# ITECH IT-M3900D user manual, quick reference pp.2–3; nominal ratings.
RATINGS = MappingProxyType({
    "IT-M3901D-10-170": Ratings(10, 170, 1700),
    "IT-M3903D-10-340": Ratings(10, 340, 3400),
    "IT-M3905D-10-510": Ratings(10, 510, 5100),
    "IT-M3910D-10-1020": Ratings(10, 1020, 10200),
    "IT-M3902D-32-80": Ratings(32, 80, 2000),
    "IT-M3904D-32-160": Ratings(32, 160, 4000),
    "IT-M3906D-32-240": Ratings(32, 240, 6000),
    "IT-M3912D-32-480": Ratings(32, 480, 12000),
    "IT-M3902D-80-40": Ratings(80, 40, 2000),
    "IT-M3904D-80-80": Ratings(80, 80, 4000),
    "IT-M3906D-80-120": Ratings(80, 120, 6000),
    "IT-M3912D-80-240": Ratings(80, 240, 12000),
    "IT-M3902D-300-20": Ratings(300, 20, 2000),
    "IT-M3904D-300-40": Ratings(300, 40, 4000),
    "IT-M3906D-300-60": Ratings(300, 60, 6000),
    "IT-M3912D-300-120": Ratings(300, 120, 12000),
    "IT-M3902D-500-12": Ratings(500, 12, 2000),
    "IT-M3904D-500-24": Ratings(500, 24, 4000),
    "IT-M3906D-500-36": Ratings(500, 36, 6000),
    "IT-M3912D-500-72": Ratings(500, 72, 12000),
    "IT-M3902D-800-8": Ratings(800, 8, 2000),
    "IT-M3904D-800-16": Ratings(800, 16, 4000),
    "IT-M3906D-800-24": Ratings(800, 24, 6000),
    "IT-M3912D-800-48": Ratings(800, 48, 12000),
    "IT-M3906D-1500-12": Ratings(1500, 12, 6000),
    "IT-M3912D-1500-24": Ratings(1500, 24, 12000),
})


class CapabilityState(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"
    UNQUALIFIED = "unqualified"


# Feature evidence, not a claim of firmware or physical qualification.
_FEATURES = ("identity", "voltage_set", "current_set", "voltage_measure",
             "current_measure", "output_control", "ovp", "ocp",
             "arb", "battery", "external_analog", "remote_sense_query")


def unknown_feature_states():
    return MappingProxyType(dict.fromkeys(_FEATURES, CapabilityState.UNKNOWN))


@dataclass(frozen=True)
class ModelDescriptor:
    model: str
    ratings: Ratings
    channels: int
    features: Mapping[str, CapabilityState]

    def state(self, feature: str) -> CapabilityState:
        return self.features.get(feature, CapabilityState.UNKNOWN)

    def require(self, feature: str) -> None:
        if self.state(feature) is not CapabilityState.SUPPORTED:
            raise UnsupportedOperationError(
                f"{self.model}: {feature} is {self.state(feature).value}"
            )


# Existing nominal-rating source only; feature/firmware guide qualification
# must be established separately. Do not turn the existence of a method into support.
MODEL_DESCRIPTORS = MappingProxyType({
    name: ModelDescriptor(name, rating, 1, MappingProxyType({
        **dict.fromkeys(_FEATURES, CapabilityState.UNQUALIFIED),
        "identity": CapabilityState.SUPPORTED,
    }))
    for name, rating in RATINGS.items()
})


def descriptor_for(identity):
    if identity.manufacturer.strip().upper() != "ITECH":
        return None
    return MODEL_DESCRIPTORS.get(identity.model.strip().upper())


@dataclass(frozen=True)
class Range:
    minimum: float
    maximum: float

    def __post_init__(self):
        if (any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                for v in (self.minimum, self.maximum))
                or self.minimum > self.maximum):
            raise ConfigurationError("range must contain ordered finite real bounds")

    def validate(self, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not self.minimum <= value <= self.maximum:
            raise ConfigurationError(f"value outside permitted range {self.minimum}..{self.maximum}: {value!r}")


@dataclass(frozen=True)
class ApplicationLimits:
    voltage: Range | None = None
    current: Range | None = None
    power: Range | None = None

    def __post_init__(self):
        for value in (self.voltage, self.current, self.power):
            if value is not None and not isinstance(value, Range):
                raise ConfigurationError("application limits must be Range or None")

    @classmethod
    def from_config(cls, config):
        """Translate persisted application bounds; never interpret them as ratings."""
        def combine(quantity, ceiling):
            raw = config.get(f"default_{quantity}_range")
            bounds = Range(*raw) if raw is not None else None
            return (intersect_range(bounds, Range(0, ceiling)) if bounds is not None
                    else Range(0, ceiling)) if ceiling is not None else bounds
        limits = config.get("safe_limits")
        power = limits["max_power"]
        return cls(combine("voltage", limits["max_voltage"]),
                   combine("current", limits["max_current"]),
                   Range(0, power) if power is not None else None)


def intersect_range(*ranges):
    if not ranges or any(not isinstance(r, Range) for r in ranges):
        raise ConfigurationError("all required operating ranges must be known")
    return Range(max(r.minimum for r in ranges), min(r.maximum for r in ranges))


@dataclass(frozen=True)
class ElectricalRanges:
    voltage: Range
    current: Range
    voltage_limit: Range
    current_limit: Range
    power_limit: Range


@dataclass(frozen=True)
class Capabilities:
    model: str
    firmware: str | None
    ratings: Ratings
    voltage: Range
    current: Range
    voltage_limit: Range
    current_limit: Range
    power_limit: Range
    live_ranges: ElectricalRanges | None = None


def effective_ranges(descriptor, live, application=None):
    """Intersect known nominal, live and optional application ranges.

    This does not imply physical qualification, nor that independently valid
    voltage/current values may be delivered simultaneously at full rating.
    """
    if not isinstance(descriptor, ModelDescriptor) or not isinstance(live, ElectricalRanges):
        raise ConfigurationError("known model descriptor and live ranges required")
    if application is None:
        application = ApplicationLimits()
    if not isinstance(application, ApplicationLimits):
        raise ConfigurationError("application limits must be ApplicationLimits")
    ratings = descriptor.ratings

    def bound(value, ceiling, user_range):
        return intersect_range(value, Range(0, ceiling),
                               *(() if user_range is None else (user_range,)))

    return ElectricalRanges(
        bound(live.voltage, ratings.voltage_v, application.voltage),
        bound(live.current, ratings.current_a, application.current),
        bound(live.voltage_limit, ratings.voltage_v, application.voltage),
        bound(live.current_limit, ratings.current_a, application.current),
        bound(live.power_limit, ratings.power_w, application.power),
    )


def discover_capabilities(driver, *, application_limits=None):
    """Explicit read-only probe; retain reported ranges separately from effective limits."""
    with driver.session.operation_lock():
        ident = driver.identity_snapshot(refresh=True)
        descriptor = descriptor_for(ident)
        if descriptor is None:
            raise IdentityError("unknown or unsupported ITECH model: " + ident.model)
        def probe(header, ceiling):
            lo = parse_float(driver.query_scpi(header + "? MIN"))
            hi = parse_float(driver.query_scpi(header + "? MAX"))
            if not 0 <= lo <= hi or hi <= 0 or lo > ceiling:
                raise ResponseParseError("invalid instrument capability range", raw=f"{lo},{hi}")
            return Range(lo, hi)
        ratings = descriptor.ratings
        live = ElectricalRanges(probe("SOUR:VOLT", ratings.voltage_v),
                                probe("SOUR:CURR", ratings.current_a),
                                probe("SOUR:VOLT:LIM", ratings.voltage_v),
                                probe("SOUR:CURR:LIM", ratings.current_a),
                                probe("SOUR:POW:LIM", ratings.power_w))
        effective = effective_ranges(descriptor, live, application_limits)
        return Capabilities(ident.model, ident.firmware_version, ratings,
                            effective.voltage, effective.current, effective.voltage_limit,
                            effective.current_limit, effective.power_limit, live)
