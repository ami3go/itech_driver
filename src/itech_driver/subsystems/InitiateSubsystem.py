from scpi_driver_core.scpi.parsers import parse_bool
from ..base import  BaseInstrument, BoolLike, Number
# -------------------------
# Initiate Subsystem (INITiate)
# -------------------------
class InitiateSubsystem:
    """INITiate commands for ACQuire, ARB, DLOG, ELOG."""
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    def acquire(self):
        self._p.write_scpi('INITiate:ACQuire')

    def arb(self):
        self._p.write_scpi('INITiate:ARB')

    def continuous_arb_set(self, enable: BoolLike):
        self._p.write_scpi(f'INITiate:CONTinuous:ARB {1 if enable else 0}')

    def continuous_arb_query(self) -> bool:  # Added: Missing query method
        return parse_bool(self._p.query_scpi('INITiate:CONTinuous:ARB?'))

    def continuous_acq_set(self, enable: BoolLike):
        self._p.write_scpi(f'INITiate:CONTinuous:ACQuire {1 if enable else 0}')

    def continuous_acq_query(self) -> bool:  # Added: Missing query method
        return parse_bool(self._p.query_scpi('INITiate:CONTinuous:ACQuire?'))

    def dlog(self):
        self._p.write_scpi('INITiate:DLOG')

    def elog(self):
        self._p.write_scpi('INITiate:ELOG')

