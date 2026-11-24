"""Rated single-unit envelopes; not firmware qualification or parallel ratings."""
from dataclasses import dataclass
from scpi_driver_core import ConfigurationError, IdentityError, ResponseParseError
from scpi_driver_core.scpi.parsers import parse_identity, parse_float


@dataclass(frozen=True)
class Ratings:
    voltage_v: float
    current_a: float
    power_w: float


# ITECH IT-M3900D user manual, quick reference pp.2–3; nominal ratings.
RATINGS = {
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
}


@dataclass(frozen=True)
class Range:
    minimum: float
    maximum: float

    def validate(self, value):
        import math
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not self.minimum <= value <= self.maximum:
            raise ConfigurationError(f"value outside permitted range {self.minimum}..{self.maximum}: {value!r}")


@dataclass(frozen=True)
class Capabilities:
    model: str
    firmware: str
    ratings: Ratings
    voltage: Range
    current: Range
    voltage_limit: Range
    current_limit: Range
    power_limit: Range


def discover_capabilities(driver):
    """Explicit read-only probe; do not change output or drain error queue."""
    with driver.session.operation_lock():
        ident = parse_identity(driver.identify())
        ratings = RATINGS.get(ident.model.strip().upper())
        if ident.manufacturer.strip().upper() != "ITECH" or ratings is None:
            raise IdentityError("unknown or unsupported ITECH model: " + ident.model)
        def probe(header, ceiling):
            lo = parse_float(driver.query_scpi(header + "? MIN"))
            hi = parse_float(driver.query_scpi(header + "? MAX"))
            if not 0 <= lo <= hi or hi <= 0 or lo > ceiling:
                raise ResponseParseError("invalid instrument capability range", raw=f"{lo},{hi}")
            return Range(lo, min(hi, ceiling))
        return Capabilities(ident.model, ident.firmware, ratings,
                            probe("SOUR:VOLT", ratings.voltage_v),
                            probe("SOUR:CURR", ratings.current_a),
                            probe("SOUR:VOLT:LIM", ratings.voltage_v),
                            probe("SOUR:CURR:LIM", ratings.current_a),
                            probe("SOUR:POW:LIM", ratings.power_w))
