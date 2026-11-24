from ..command_specs import execute, execute_parameterized, command_spec
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
        execute(self._p, "TriggerSubsystem.acquire_immediate")

    def acquire_arm(self):
        """Initiate the measurement trigger system, without generating a trigger.

        Guide p.105: readiness takes a few milliseconds; a premature trigger
        may be ignored. Successful transmission is not readiness confirmation.
        """
        execute(self._p, "TriggerSubsystem.acquire_arm")

    def acquire_start(self, source: str = "EXT"):
        """Configure and arm only. Call the appropriate trigger separately."""
        token = self._normalize_source("ACQ", source)
        with self._p.session.operation_lock():
            self._p._require_methods("TriggerSubsystem.acquire_source_set", "TriggerSubsystem.acquire_arm")
            self.acquire_source_set(token)
            self.acquire_arm()

    def acquire_mode_set(self, mode: str):
        execute_parameterized(self._p, "TriggerSubsystem.acquire_mode_set", mode)

    def acquire_mode_query(self) -> str:
        return execute(self._p, "TriggerSubsystem.acquire_mode_query")

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
        name = {"ACQ": "acquire", "ARB": "arb", "DLOG": "dlog", "ELOG": "elog"}[subsystem]
        execute_parameterized(self._p, f"TriggerSubsystem.{name}_source_set", token)

    def _source_query(self, subsystem: str) -> str:
        name = {"ACQ": "acquire", "ARB": "arb", "DLOG": "dlog", "ELOG": "elog"}[subsystem]
        raw = execute(self._p, f"TriggerSubsystem.{name}_source_query")
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
    def _numeric_arg(value: Number) -> Number:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ConfigurationError("trigger level must be a finite real number")
        if value < 0:
            raise ConfigurationError("trigger level must be nonnegative")
        return value

    def acquire_voltage_level_set(self, value: Number):
        execute_parameterized(self._p, "TriggerSubsystem.acquire_voltage_level_set", self._numeric_arg(value))

    def acquire_voltage_level_query(self) -> float:
        return execute(self._p, "TriggerSubsystem.acquire_voltage_level_query")

    def acquire_current_level_set(self, value: Number):
        execute_parameterized(self._p, "TriggerSubsystem.acquire_current_level_set", self._numeric_arg(value))

    def acquire_current_level_query(self) -> float:
        return execute(self._p, "TriggerSubsystem.acquire_current_level_query")

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
        return command_spec("TriggerSubsystem.hysteresis_threshold_set").header.format(subsystem=subsystem, quantity=quantity, bound=bound)

    def hysteresis_threshold_query(self, subsystem: str, quantity: str, bound: str) -> float:
        header = self._hysteresis_header(subsystem, quantity, bound)
        query = command_spec("TriggerSubsystem.hysteresis_threshold_query").header.format(subsystem=subsystem, quantity=quantity, bound=bound)
        return parse_float(self._p.query_scpi(query))

    def hysteresis_threshold_set(self, subsystem: str, quantity: str, bound: str, value: Number):
        header = self._hysteresis_header(subsystem, quantity, bound)
        arg = self._numeric_arg(value)
        other = "LOW" if bound == "HIGH" else "HIGH"
        # Driver-side ordering guard; independent controllers may change settings.
        with self._p.session.operation_lock():
            self._p._require_methods("TriggerSubsystem.hysteresis_threshold_query")
            self._p._assert_write_authorized()
            opposite = self.hysteresis_threshold_query(subsystem, quantity, other)
            if (bound == "HIGH" and value < opposite) or (bound == "LOW" and value > opposite):
                raise ConfigurationError("high trigger threshold must be >= low threshold")
            self._p.write_scpi(f"{header} {arg}")

    def elog_trigger_voltage_high_set(self, val: Number):
        self.hysteresis_threshold_set("ELOG", "VOLT", "HIGH", val)

    def elog_trigger_voltage_low_set(self, val: Number):
        self.hysteresis_threshold_set("ELOG", "VOLT", "LOW", val)

    def elog_status_query(self) -> str:
        return execute(self._p, "TriggerSubsystem.elog_status_query")  # Separate ELOG qualification required.

    def hysteresis_set(self, val: Number):
        raise UnsupportedOperationError("specify subsystem, quantity and high/low threshold")

    def hysteresis_query(self) -> float:
        raise UnsupportedOperationError("specify subsystem, quantity and high/low threshold")
