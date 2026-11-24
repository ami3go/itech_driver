from scpi_driver_core.scpi.parsers import parse_int
from ..base import  BaseInstrument, BoolLike, Number
# -------------------------
# Status Subsystem (STATus)
# -------------------------
class StatusSubsystem:
    """Status registers (Operation, Questionable, Standard Event)."""
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    def preset(self):
        """Preset status register masks; not an instrument reset."""
        self._p.write_scpi('STAT:PRES')

    # Operation
    def oper_condition_query(self) -> int:
        return parse_int(self._p.query_scpi('STAT:OPER:COND?'))

    def oper_enable_set(self, mask: int):
        self._p.write_scpi(f'STAT:OPER:ENAB {int(mask)}')

    def oper_enable_query(self) -> int:
        return parse_int(self._p.query_scpi('STAT:OPER:ENAB?'))

    def oper_event_query(self) -> int:
        return parse_int(self._p.query_scpi('STAT:OPER:EVEN?'))

    # Questionable
    def ques_condition_query(self) -> int:
        return parse_int(self._p.query_scpi('STAT:QUES:COND?'))

    def ques_enable_set(self, mask: int):
        self._p.write_scpi(f'STAT:QUES:ENAB {int(mask)}')

    def ques_enable_query(self) -> int:
        return parse_int(self._p.query_scpi('STAT:QUES:ENAB?'))

    def ques_event_query(self) -> int:
        return parse_int(self._p.query_scpi('STAT:QUES:EVEN?'))

    # Standard event - Corrected: SETR should be ESET
    def std_event_enable_set(self, mask: int):
        self._p.write_scpi(f'*ESE {int(mask)}')  # Standard IEEE command

    def std_event_enable_query(self) -> int:  # Added: Missing query method
        return parse_int(self._p.query_scpi('*ESE?'))

    def std_event_register_query(self) -> int:  # Added: Standard event register query
        return parse_int(self._p.query_scpi('*ESR?'))

    def status_byte(self) -> int:
        return parse_int(self._p.query_scpi('*STB?'))

