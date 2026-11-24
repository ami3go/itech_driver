"""Offline ARB command plans; never contact hardware.
Guide V1.4/09,2024, indexed pp.230–235. Full parameter ranges and firmware
readback are not yet qualified. Plans contain parameter setters only.
"""
from dataclasses import dataclass
import math
from scpi_driver_core import ConfigurationError


def number(value, name, *, positive=False):
    if isinstance(value, bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ConfigurationError(f"{name} must be finite and numeric")
    if value < 0 or (positive and value == 0):
        raise ConfigurationError(f"{name} outside supported offline range")
    return value


@dataclass(frozen=True)
class Envelope:
    """Explicit caller-supplied limits; not a hardware capability assertion."""
    max_level: float
    min_time_s: float
    max_time_s: float

    def __post_init__(self):
        number(self.max_level,"max_level",positive=True)
        number(self.min_time_s,"min_time_s")
        number(self.max_time_s,"max_time_s",positive=True)
        if self.min_time_s > self.max_time_s:
            raise ConfigurationError("invalid time range")

    def level(self,value):
        if number(value,"level") > self.max_level:
            raise ConfigurationError("level exceeds caller envelope")
        return value

    def duration(self,value):
        if not self.min_time_s <= number(value,"duration") <= self.max_time_s:
            raise ConfigurationError("duration outside caller envelope")
        return value


@dataclass(frozen=True)
class Pulse:
    start_level: float
    start_time_s: float
    start_slew_s: float
    top_level: float
    top_time_s: float
    end_time_s: float
    end_slew_s: float

    def commands(self, envelope: Envelope) -> tuple[str,...]:
        """Build candidate native parameter commands, not shape/trigger/output commands."""
        if not isinstance(envelope, Envelope):
            raise ConfigurationError("explicit envelope required")
        fields = (
            ("STAR:LEV",envelope.level(self.start_level)),
            ("STAR:TIME",envelope.duration(self.start_time_s)),
            ("STAR:SLEW",envelope.duration(self.start_slew_s)),
            ("TOP:LEV",envelope.level(self.top_level)),
            ("TOP:TIME",envelope.duration(self.top_time_s)),
            ("END:TIME",envelope.duration(self.end_time_s)),
            ("END:SLEW",envelope.duration(self.end_slew_s)),
        )
        return tuple(f"ARB:PULS:{header} {value}" for header,value in fields)
