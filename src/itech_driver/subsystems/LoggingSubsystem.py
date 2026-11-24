"""Logging configuration and raw status; no implicit start/stop."""
from dataclasses import dataclass
import math
from scpi_driver_core import ConfigurationError, ResponseParseError


@dataclass(frozen=True)
class LoggingConfig:
    voltage: bool
    current: bool
    peak: bool
    period: float
    duration: float

    def commands(self, kind, *, min_period, max_period, max_duration):
        if kind not in ("ELOG","DLOG"):
            raise ConfigurationError("invalid logging subsystem")
        if any(type(v) is not bool for v in (self.voltage,self.current,self.peak)):
            raise ConfigurationError("logging flags must be boolean")
        if not (self.voltage or self.current):
            raise ConfigurationError("select at least one measurement quantity")
        vals = (self.period,self.duration,min_period,max_period,max_duration)
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v <= 0 for v in vals):
            raise ConfigurationError("explicit finite positive timing bounds required")
        if not min_period <= self.period <= max_period or not self.period <= self.duration <= max_duration:
            raise ConfigurationError("logging timing outside caller envelope")
        prefix = f"SENS:{kind}"
        return (f"{prefix}:FUNC:VOLT {int(self.voltage)}",
                f"{prefix}:FUNC:CURR {int(self.current)}",
                f"{prefix}:FUNC:PEAK {int(self.peak)}",
                f"{prefix}:PER {self.period}",f"{prefix}:TIME {self.duration}")


class LoggingSubsystem:
    def __init__(self,parent,kind):
        if kind not in ("ELOG","DLOG"):
            raise ConfigurationError("invalid logging subsystem")
        self._p = parent
        self._kind = kind

    def state_query(self):
        """Raw status only; do not infer readiness, completion, or stop."""
        raw = self._p.query_scpi(f"{self._kind}:STAT?").strip()
        if not raw:
            raise ResponseParseError("empty logging state",raw=raw)
        return raw

    def raw_data_query(self, *, ascii_confirmed=False):
        """Unparsed ELOG data; exact record layout is not qualified."""
        if self._kind != "ELOG" or ascii_confirmed is not True:
            raise ConfigurationError("ELOG ASCII response format must be confirmed")
        raw = self._p.query_scpi("FETC:ELOG:ARR:DATA?")
        if not raw.strip():
            raise ResponseParseError("empty ELOG data",raw=raw)
        return raw
