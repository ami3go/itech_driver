"""Logging configuration and raw status; no implicit start/stop."""
from dataclasses import dataclass
import math
from scpi_driver_core import ConfigurationError, ResponseParseError
from ..command_specs import command_spec, LOGGING_CONFIG_TEMPLATES


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
        return tuple(template.format(kind=kind, value=value) for template, value in
                     zip(LOGGING_CONFIG_TEMPLATES, (int(self.voltage), int(self.current), int(self.peak), self.period, self.duration)))


class LoggingSubsystem:
    def __init__(self,parent,kind):
        if kind not in ("ELOG","DLOG"):
            raise ConfigurationError("invalid logging subsystem")
        self._p = parent
        self._kind = kind

    def state_query(self):
        """Raw status only; do not infer readiness, completion, or stop."""
        raw = self._p.query_scpi(command_spec("LoggingSubsystem.state_query").header.format(kind=self._kind)).strip()
        if not raw:
            raise ResponseParseError("empty logging state",raw=raw)
        return raw

    def raw_data_query(self, *, ascii_confirmed=False):
        """Unparsed ELOG data; exact record layout is not qualified."""
        if self._kind != "ELOG" or ascii_confirmed is not True:
            raise ConfigurationError("ELOG ASCII response format must be confirmed")
        raw = self._p.query_scpi(command_spec("LoggingSubsystem.raw_data_query").header)
        if not raw.strip():
            raise ResponseParseError("empty ELOG data",raw=raw)
        return raw
