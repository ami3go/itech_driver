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

    def source_set(self, src: str):
        self._p.write_scpi(f'TRIG:SOUR {src}')

    def source_query(self) -> str:
        return self._p.query_scpi('TRIG:SOUR?')

    def level_set(self, val: Number):
        self._p.write_scpi(f'TRIG:LEV {val}')

    def level_query(self) -> float:
        return parse_float(self._p.query_scpi('TRIG:LEV?'))

    def delay_set(self, seconds: Number):
        self._p.write_scpi(f'TRIG:DEL {seconds}')

    def delay_query(self) -> float:
        return parse_float(self._p.query_scpi('TRIG:DEL?'))

    # ELOG related
    def elog_trigger_voltage_high_set(self, val: Number):
        self._p.write_scpi(f'TRIG:ELOG:VOLTage:HYSTeresis:HIGH {val}')

    def elog_trigger_voltage_low_set(self, val: Number):
        self._p.write_scpi(f'TRIG:ELOG:VOLTage:HYSTeresis:LOW {val}')

    def elog_status_query(self) -> str:
        return self._p.query_scpi('ELOG:STAT?')  # Note: This might need TRIG: prefix

    def hysteresis_set(self, val: Number):  # Added: General hysteresis setting
        self._p.write_scpi(f'TRIG:HYSTeresis {val}')

    def hysteresis_query(self) -> float:  # Added: General hysteresis query
        return parse_float(self._p.query_scpi('TRIG:HYSTeresis?'))

