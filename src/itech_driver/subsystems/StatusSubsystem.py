from scpi_driver_core import ConfigurationError, ResponseParseError
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
        self._mask_set('STAT:OPER:ENAB', mask)

    def oper_enable_query(self) -> int:
        return self._mask_query('STAT:OPER:ENAB')

    def oper_event_query(self) -> int:
        return parse_int(self._p.query_scpi('STAT:OPER:EVEN?'))

    # Questionable
    def ques_condition_query(self) -> int:
        return parse_int(self._p.query_scpi('STAT:QUES:COND?'))

    def ques_enable_set(self, mask: int):
        self._mask_set('STAT:QUES:ENAB', mask)

    def ques_enable_query(self) -> int:
        return self._mask_query('STAT:QUES:ENAB')

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


    def _mask_set(self, header: str, mask: int):
        if type(mask) is not int or not 0 <= mask <= 65535:
            raise ConfigurationError("transition mask must be an integer in 0..65535")
        self._p.write_scpi(f"{header} {mask}")

    def _mask_query(self, header: str) -> int:
        raw = self._p.query_scpi(header + "?")
        mask = parse_int(raw)
        if not 0 <= mask <= 65535:
            raise ResponseParseError("invalid 16-bit status mask", raw=raw)
        return mask

    def oper_positive_transition_set(self, mask: int):
        self._mask_set("STAT:OPER:PTR", mask)

    def oper_positive_transition_query(self) -> int:
        return self._mask_query("STAT:OPER:PTR")

    def oper_negative_transition_set(self, mask: int):
        self._mask_set("STAT:OPER:NTR", mask)

    def oper_negative_transition_query(self) -> int:
        return self._mask_query("STAT:OPER:NTR")

    def ques_positive_transition_set(self, mask: int):
        self._mask_set("STAT:QUES:PTR", mask)

    def ques_positive_transition_query(self) -> int:
        return self._mask_query("STAT:QUES:PTR")

    def ques_negative_transition_set(self, mask: int):
        self._mask_set("STAT:QUES:NTR", mask)

    def ques_negative_transition_query(self) -> int:
        return self._mask_query("STAT:QUES:NTR")
