from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.scpi.parsers import parse_bool, parse_float, parse_int
from typing import Optional
from ..base import  BaseInstrument, BoolLike, Number
from ..utils.validation import validate_channel, strict_bool
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
        self._p.write_scpi(f'OUTP:STAT {"ON" if on else "OFF"}')

    def state_query(self, channel: int = 1) -> bool:
        self._check_channel(channel)
        return parse_bool(self._p.query_scpi('OUTP:STAT?'))

    def delay_rise_set(self, seconds: Number):
        self._p.write_scpi(f'OUTP:DELay:RISE {seconds}')

    def delay_rise_query(self) -> float:
        return parse_float(self._p.query_scpi('OUTP:DELay:RISE?'))

    def delay_fall_set(self, seconds: Number):
        self._p.write_scpi(f'OUTP:DELay:FALL {seconds}')

    def delay_fall_query(self) -> float:
        return parse_float(self._p.query_scpi('OUTP:DELay:FALL?'))

    def inhibit_mode_set(self, mode: str):
        self._p.write_scpi(f'OUTP:INHibit:MODE {mode}')

    def inhibit_mode_query(self) -> str:  # Added: Missing query method
        return self._p.query_scpi('OUTP:INHibit:MODE?')

    def protection_clear(self):
        self._p.write_scpi('OUTP:PROTection:CLEar')

    def watchdog_set(self, enable: BoolLike, delay_s: Optional[int] = None):
        """Verify configuration and final watchdog state; never infer physical output state."""
        enable = strict_bool(enable, "watchdog state")
        if delay_s is not None and (type(delay_s) is not int or not 1 <= delay_s <= 3600):
            raise ConfigurationError("watchdog delay must be an integer in 1..3600 seconds")
        with self._p.session.operation_lock():
            self._p._assert_write_authorized()
            if not enable:
                self._p.write_scpi("OUTP:PROT:WDOG:STAT 0")
                if self.watchdog_query() is not False:
                    raise ResponseParseError("watchdog disable readback mismatch", raw="ON")
            if delay_s is not None:
                self._p.write_scpi(f"OUTP:PROT:WDOG:DEL {delay_s}")
                actual = self.watchdog_delay_query()
                if actual != delay_s:
                    raise ResponseParseError("watchdog delay readback mismatch", raw=str(actual))
            elif enable:
                self.watchdog_delay_query()
            if enable:
                self._p.write_scpi("OUTP:PROT:WDOG:STAT 1")
                if self.watchdog_query() is not True:
                    raise ResponseParseError("watchdog enable readback mismatch", raw="OFF")
            elif delay_s is not None and self.watchdog_query() is not False:
                raise ResponseParseError("watchdog changed state during delay configuration", raw="ON")

    def watchdog_query(self) -> bool:
        return parse_bool(self._p.query_scpi('OUTP:PROT:WDOG:STAT?'))

    def watchdog_delay_query(self) -> int:
        raw = self._p.query_scpi('OUTP:PROT:WDOG:DEL?')
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
        self._p.write_scpi(f"OUTP:PON:STAT {token}")

    def power_on_mode_query(self) -> str:
        raw = self._p.query_scpi("OUTP:PON:STAT?").strip().upper()
        if raw not in ("RST", "LAST_ON", "LAST_OFF"):
            raise ResponseParseError("invalid power-on mode response", raw=raw)
        return raw
