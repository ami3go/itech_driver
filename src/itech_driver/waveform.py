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


@dataclass(frozen=True)
class Sine:
    peak_to_peak: float
    offset: float
    frequency_hz: float

    def commands(self, envelope: Envelope, *, min_frequency_hz: float,
                 max_frequency_hz: float, amplitude_convention: str) -> tuple[str,...]:
        """Build offline parameter plan; AMPL convention requires explicit confirmation."""
        if not isinstance(envelope, Envelope):
            raise ConfigurationError("explicit envelope required")
        pp = number(self.peak_to_peak,"peak-to-peak")
        offset = number(self.offset,"offset")
        envelope.level(offset - pp / 2)
        envelope.level(offset + pp / 2)
        lo = number(min_frequency_hz,"minimum frequency",positive=True)
        hi = number(max_frequency_hz,"maximum frequency",positive=True)
        freq = number(self.frequency_hz,"frequency",positive=True)
        if not lo <= freq <= hi:
            raise ConfigurationError("frequency outside caller envelope")
        if amplitude_convention not in ("peak_to_peak", "peak"):
            raise ConfigurationError("explicit confirmed SCPI amplitude convention required")
        amplitude = pp if amplitude_convention == "peak_to_peak" else pp / 2
        return (f"ARB:SIN:AMPL {amplitude}", f"ARB:SIN:OFFS {offset}",
                f"ARB:SIN:FREQ {freq}")


@dataclass(frozen=True)
class Sweep:
    peak_to_peak: float
    offset: float
    start_hz: float
    end_hz: float
    step_hz: float
    step_width_s: float

    def commands(self, envelope: Envelope, *, min_frequency_hz: float,
                 max_frequency_hz: float, amplitude_convention: str,
                 max_steps: int) -> tuple[str,...]:
        """Candidate setter plan, no implicit execution or cycle conversion."""
        if type(max_steps) is not int or max_steps < 2:
            raise ConfigurationError("explicit positive step budget required")
        start = number(self.start_hz,"start frequency",positive=True)
        end = number(self.end_hz,"end frequency",positive=True)
        step = number(self.step_hz,"frequency increment",positive=True)
        if end <= start or step > end-start:
            raise ConfigurationError("require increasing sweep and bounded step")
        ratio = (end-start)/step
        if not math.isfinite(ratio) or ratio > max_steps-1:
            raise ConfigurationError("sweep exceeds step budget")
        sine = Sine(self.peak_to_peak,self.offset,start).commands(
            envelope,min_frequency_hz=min_frequency_hz,
            max_frequency_hz=max_frequency_hz,amplitude_convention=amplitude_convention)
        Sine(self.peak_to_peak,self.offset,end).commands(
            envelope,min_frequency_hz=min_frequency_hz,
            max_frequency_hz=max_frequency_hz,amplitude_convention=amplitude_convention)
        width = envelope.duration(self.step_width_s)
        number(width,"step width",positive=True)
        return (sine[0].replace("ARB:SIN:","ARB:SWE:"),
                sine[1].replace("ARB:SIN:","ARB:SWE:"),
                f"ARB:SWE:STAR {start}",f"ARB:SWE:END {end}",
                f"ARB:SWE:STEP:LEV {step}",f"ARB:SWE:STEP:WIDT {width}")
