from scpi_driver_core.scpi.parsers import parse_bool, parse_float, parse_int
from typing import Optional
from ..base import  BaseInstrument, BoolLike, Number
# -------------------------
# Output Subsystem (OUTPut)
# -------------------------
class OutputSubsystem:
    """Output settings: state, delays, protections."""
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    def state_set(self, on: BoolLike, channel: int = 1):
        self._p.write_scpi(f'OUTP{channel}:STAT {"ON" if on else "OFF"}')

    def state_query(self, channel: int = 1) -> bool:
        return parse_bool(self._p.query_scpi(f'OUTP{channel}:STAT?'))

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
        self._p.write_scpi(f'OUTP:PROT:WDOG:STAT {1 if enable else 0}')
        if delay_s is not None:
            self._p.write_scpi(f'OUTP:PROT:WDOG:DEL {int(delay_s)}')

    def watchdog_query(self) -> bool:  # Added: Missing query method
        return parse_bool(self._p.query_scpi('OUTP:PROT:WDOG:STAT?'))

    def watchdog_delay_query(self) -> int:  # Added: Missing query method
        return parse_int(self._p.query_scpi('OUTP:PROT:WDOG:DEL?'))
