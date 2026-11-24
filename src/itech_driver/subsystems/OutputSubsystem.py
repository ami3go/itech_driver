from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.scpi.parsers import parse_bool, parse_float, parse_int
from typing import Optional
from ..base import  BaseInstrument, BoolLike, Number
from ..utils.validation import validate_channel, strict_bool
from ..command_specs import execute, execute_parameterized, command_spec
# -------------------------
# Output Subsystem (OUTPut)
# -------------------------
class OutputSubsystem:
    """Output settings: state, delays, protections."""
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    @staticmethod
    def _check_channel(channel: int) -> None:
        validate_channel(channel, 1)

    def state_set(self, on: BoolLike, channel: int = 1):
        self._check_channel(channel)
        on = strict_bool(on, "output state")
        execute(self._p, "OutputSubsystem.state_set", on)

    def state_query(self, channel: int = 1) -> bool:
        self._check_channel(channel)
        return execute(self._p, "OutputSubsystem.state_query")

    def delay_rise_set(self, seconds: Number):
        execute_parameterized(self._p, "OutputSubsystem.delay_rise_set", seconds)

    def delay_rise_query(self) -> float:
        return execute(self._p, "OutputSubsystem.delay_rise_query")

    def delay_fall_set(self, seconds: Number):
        execute_parameterized(self._p, "OutputSubsystem.delay_fall_set", seconds)

    def delay_fall_query(self) -> float:
        return execute(self._p, "OutputSubsystem.delay_fall_query")

    def inhibit_mode_set(self, mode: str):
        execute_parameterized(self._p, "OutputSubsystem.inhibit_mode_set", mode)

    def inhibit_mode_query(self) -> str:  # Added: Missing query method
        return execute(self._p, "OutputSubsystem.inhibit_mode_query")

    def protection_clear(self):
        execute(self._p, "OutputSubsystem.protection_clear")

    def watchdog_set(self, enable: BoolLike, delay_s: Optional[int] = None):
        """Verify configuration and final watchdog state; never infer physical output state."""
        enable = strict_bool(enable, "watchdog state")
        if delay_s is not None and (type(delay_s) is not int or not 1 <= delay_s <= 3600):
            raise ConfigurationError("watchdog delay must be an integer in 1..3600 seconds")
        with self._p.session.operation_lock():
            self._p._require_methods("OutputSubsystem.watchdog_query", *(() if delay_s is None and not enable else ("OutputSubsystem.watchdog_delay_query",)))
            self._p._assert_write_authorized()
            state_header = command_spec("OutputSubsystem.watchdog_query").header.removesuffix("?")
            delay_header = command_spec("OutputSubsystem.watchdog_delay_query").header.removesuffix("?")
            if not enable:
                self._p.write_scpi(state_header + " 0")
                if self.watchdog_query() is not False:
                    raise ResponseParseError("watchdog disable readback mismatch", raw="ON")
            if delay_s is not None:
                self._p.write_scpi(f"{delay_header} {delay_s}")
                actual = self.watchdog_delay_query()
                if actual != delay_s:
                    raise ResponseParseError("watchdog delay readback mismatch", raw=str(actual))
            elif enable:
                self.watchdog_delay_query()
            if enable:
                self._p.write_scpi(state_header + " 1")
                if self.watchdog_query() is not True:
                    raise ResponseParseError("watchdog enable readback mismatch", raw="OFF")
            elif delay_s is not None and self.watchdog_query() is not False:
                raise ResponseParseError("watchdog changed state during delay configuration", raw="ON")

    def watchdog_query(self) -> bool:
        return execute(self._p, "OutputSubsystem.watchdog_query")

    def watchdog_delay_query(self) -> int:
        raw = execute(self._p, "OutputSubsystem.watchdog_delay_query")
        value = parse_float(raw)
        if not value.is_integer() or not 1 <= value <= 3600:
            raise ResponseParseError("invalid watchdog delay response", raw=raw)
        return int(value)

    def power_on_mode_set(self, mode: str, *, allow_restore_output: bool = False):
        """Set startup policy, never switch output on as part of this method.

        LAST_ON can restore a previously enabled output on a later power cycle.
        It requires explicit acknowledgment; LAST_OFF preserves settings with
        output disabled. RST restores the factory startup settings.
        """
        token = mode.upper() if isinstance(mode, str) else None
        if token not in ("RST", "LAST_ON", "LAST_OFF"):
            raise ConfigurationError("power-on mode must be RST, LAST_ON or LAST_OFF")
        if token == "LAST_ON" and allow_restore_output is not True:
            raise ConfigurationError("LAST_ON requires explicit allow_restore_output=True")
        execute_parameterized(self._p, "OutputSubsystem.power_on_mode_set", token)

    def power_on_mode_query(self) -> str:
        raw = execute(self._p, "OutputSubsystem.power_on_mode_query").strip().upper()
        if raw not in ("RST", "LAST_ON", "LAST_OFF"):
            raise ResponseParseError("invalid power-on mode response", raw=raw)
        return raw
