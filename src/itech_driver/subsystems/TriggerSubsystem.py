import math
from scpi_driver_core import ConfigurationError, ResponseParseError, UnsupportedOperationError
from scpi_driver_core.scpi.parsers import parse_float
from ..base import  BaseInstrument, BoolLike, Number
# -------------------------
# Trigger Subsystem (TRIGger)
# -------------------------
class TriggerSubsystem:
    """Trigger subsystem (ACQuire, ELOG, external, levels & hysteresis, etc.)."""
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    def acquire_immediate(self):
        self._p.write_scpi('TRIG:ACQuire:IMMediate')

    def acquire_start(self, source: str = 'EXT'):
        self._p.write_scpi(f'TRIG:ACQ:SOUR {source}')
        self._p.write_scpi('TRIG:ACQ')

    def acquire_mode_set(self, mode: str):
        self._p.write_scpi(f'TRIG:ACQ:MODE {mode}')

    def acquire_mode_query(self) -> str:
        return self._p.query_scpi('TRIG:ACQ:MODE?')

    _SOURCE_ALIASES = {
        "VOLT": "VOLT", "VOLTAGE": "VOLT",
        "CURR": "CURR", "CURRENT": "CURR",
        "EXT": "EXT", "EXTERNAL": "EXT",
        "BUS": "BUS", "MAN": "MAN", "MANUAL": "MAN",
        "IMM": "IMM", "IMMEDIATE": "IMM",
    }
    _SOURCES = {
        "ACQ": frozenset(("VOLT", "CURR", "EXT", "BUS", "MAN", "IMM")),
        "ARB": frozenset(("EXT", "BUS", "MAN", "IMM")),
        "DLOG": frozenset(("VOLT", "CURR", "EXT", "BUS", "MAN", "IMM")),
        "ELOG": frozenset(("VOLT", "CURR", "EXT", "BUS", "MAN", "IMM")),
    }

    @classmethod
    def _normalize_source(cls, subsystem: str, source: str) -> str:
        token = cls._SOURCE_ALIASES.get(source.upper()) if isinstance(source, str) else None
        if token not in cls._SOURCES[subsystem]:
            raise ConfigurationError(f"invalid {subsystem} trigger source: {source!r}")
        return token

    def _source_set(self, subsystem: str, source: str):
        token = self._normalize_source(subsystem, source)
        self._p.write_scpi(f"TRIG:{subsystem}:SOUR {token}")

    def _source_query(self, subsystem: str) -> str:
        raw = self._p.query_scpi(f"TRIG:{subsystem}:SOUR?")
        try:
            return self._normalize_source(subsystem, raw.strip())
        except ConfigurationError as exc:
            raise ResponseParseError(f"invalid {subsystem} trigger source response", raw=raw) from exc

    def acquire_source_set(self, source: str):
        self._source_set("ACQ", source)

    def acquire_source_query(self) -> str:
        return self._source_query("ACQ")

    def arb_source_set(self, source: str):
        self._source_set("ARB", source)

    def arb_source_query(self) -> str:
        return self._source_query("ARB")

    def dlog_source_set(self, source: str):
        self._source_set("DLOG", source)

    def dlog_source_query(self) -> str:
        return self._source_query("DLOG")

    def elog_source_set(self, source: str):
        self._source_set("ELOG", source)

    def elog_source_query(self) -> str:
        return self._source_query("ELOG")

    def source_set(self, src: str):
        raise UnsupportedOperationError("select an explicit ACQ, ARB, DLOG or ELOG trigger source")

    def source_query(self) -> str:
        raise UnsupportedOperationError("select an explicit ACQ, ARB, DLOG or ELOG trigger source")

    @staticmethod
    def _numeric_arg(value: Number) -> str:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ConfigurationError("trigger level must be a finite real number")
        if value < 0:
            raise ConfigurationError("trigger level must be nonnegative")
        return str(value)

    def acquire_voltage_level_set(self, value: Number):
        self._p.write_scpi(f"TRIG:ACQ:VOLT:LEV {self._numeric_arg(value)}")

    def acquire_voltage_level_query(self) -> float:
        return parse_float(self._p.query_scpi("TRIG:ACQ:VOLT:LEV?"))

    def acquire_current_level_set(self, value: Number):
        self._p.write_scpi(f"TRIG:ACQ:CURR:LEV {self._numeric_arg(value)}")

    def acquire_current_level_query(self) -> float:
        return parse_float(self._p.query_scpi("TRIG:ACQ:CURR:LEV?"))

    def level_set(self, val: Number):
        raise UnsupportedOperationError("select explicit acquisition voltage or current level")

    def level_query(self) -> float:
        raise UnsupportedOperationError("select explicit acquisition voltage or current level")

    def delay_set(self, seconds: Number):
        raise UnsupportedOperationError("generic trigger delay is not documented for IT-M3900D")

    def delay_query(self) -> float:
        raise UnsupportedOperationError("generic trigger delay is not documented for IT-M3900D")

    @staticmethod
    def _hysteresis_header(subsystem: str, quantity: str, bound: str) -> str:
        if subsystem not in ("ACQ", "DLOG", "ELOG"):
            raise ConfigurationError("hysteresis subsystem must be ACQ, DLOG or ELOG")
        if quantity not in ("VOLT", "CURR"):
            raise ConfigurationError("hysteresis quantity must be VOLT or CURR")
        if bound not in ("HIGH", "LOW"):
            raise ConfigurationError("hysteresis bound must be HIGH or LOW")
        return f"TRIG:{subsystem}:{quantity}:HYST:{bound}"

    def hysteresis_threshold_query(self, subsystem: str, quantity: str, bound: str) -> float:
        header = self._hysteresis_header(subsystem, quantity, bound)
        return parse_float(self._p.query_scpi(f"{header}?"))

    def hysteresis_threshold_set(self, subsystem: str, quantity: str, bound: str, value: Number):
        header = self._hysteresis_header(subsystem, quantity, bound)
        arg = self._numeric_arg(value)
        other = "LOW" if bound == "HIGH" else "HIGH"
        # Driver-side ordering guard; independent controllers may change settings.
        with self._p.session.operation_lock():
            opposite = self.hysteresis_threshold_query(subsystem, quantity, other)
            if (bound == "HIGH" and value < opposite) or (bound == "LOW" and value > opposite):
                raise ConfigurationError("high trigger threshold must be >= low threshold")
            self._p.write_scpi(f"{header} {arg}")

    def elog_trigger_voltage_high_set(self, val: Number):
        self.hysteresis_threshold_set("ELOG", "VOLT", "HIGH", val)

    def elog_trigger_voltage_low_set(self, val: Number):
        self.hysteresis_threshold_set("ELOG", "VOLT", "LOW", val)

    def elog_status_query(self) -> str:
        return self._p.query_scpi('ELOG:STAT?')  # Separate ELOG qualification required.

    def hysteresis_set(self, val: Number):
        raise UnsupportedOperationError("specify subsystem, quantity and high/low threshold")

    def hysteresis_query(self) -> float:
        raise UnsupportedOperationError("specify subsystem, quantity and high/low threshold")
