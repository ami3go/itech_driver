from ..command_specs import execute, execute_parameterized, command_spec
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
        execute(self._p, "StatusSubsystem.preset")

    # Operation
    def oper_condition_query(self) -> int:
        return execute(self._p, "StatusSubsystem.oper_condition_query")

    def oper_enable_set(self, mask: int):
        self._mask_set(command_spec("StatusSubsystem.oper_enable_set").header, mask)

    def oper_enable_query(self) -> int:
        return self._mask_query(command_spec("StatusSubsystem.oper_enable_query").header)

    def oper_event_query(self) -> int:
        return execute(self._p, "StatusSubsystem.oper_event_query")

    # Questionable
    def ques_condition_query(self) -> int:
        return execute(self._p, "StatusSubsystem.ques_condition_query")

    def ques_enable_set(self, mask: int):
        self._mask_set(command_spec("StatusSubsystem.ques_enable_set").header, mask)

    def ques_enable_query(self) -> int:
        return self._mask_query(command_spec("StatusSubsystem.ques_enable_query").header)

    def ques_event_query(self) -> int:
        return execute(self._p, "StatusSubsystem.ques_event_query")

    # Standard event - Corrected: SETR should be ESET
    def std_event_enable_set(self, mask: int):
        return self._p._invoke_ieee(self._p.session.ieee488.set_event_status_enable, mask, write=True)

    def std_event_enable_query(self) -> int:  # Added: Missing query method
        return self._p._invoke_ieee(self._p.session.ieee488.query_event_status_enable)

    def std_event_register_query(self) -> int:  # Added: Standard event register query
        return self._p._invoke_ieee(self._p.session.ieee488.read_event_status)

    def status_byte(self) -> int:
        return self._p._invoke_ieee(self._p.session.ieee488.query_status_byte)


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
        self._mask_set(command_spec("StatusSubsystem.oper_positive_transition_set").header, mask)

    def oper_positive_transition_query(self) -> int:
        return self._mask_query(command_spec("StatusSubsystem.oper_positive_transition_query").header)

    def oper_negative_transition_set(self, mask: int):
        self._mask_set(command_spec("StatusSubsystem.oper_negative_transition_set").header, mask)

    def oper_negative_transition_query(self) -> int:
        return self._mask_query(command_spec("StatusSubsystem.oper_negative_transition_query").header)

    def ques_positive_transition_set(self, mask: int):
        self._mask_set(command_spec("StatusSubsystem.ques_positive_transition_set").header, mask)

    def ques_positive_transition_query(self) -> int:
        return self._mask_query(command_spec("StatusSubsystem.ques_positive_transition_query").header)

    def ques_negative_transition_set(self, mask: int):
        self._mask_set(command_spec("StatusSubsystem.ques_negative_transition_set").header, mask)

    def ques_negative_transition_query(self) -> int:
        return self._mask_query(command_spec("StatusSubsystem.ques_negative_transition_query").header)
