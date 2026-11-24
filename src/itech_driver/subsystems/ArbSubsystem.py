from scpi_driver_core import ResponseParseError
from scpi_driver_core.scpi.parsers import parse_bool, parse_float, parse_int
from ..base import  BaseInstrument, BoolLike, Number
# -------------------------
# ARB / List Subsystem (ARB)
# -------------------------
class ArbSubsystem:
    """ARB / List / Sequence programming and execution."""
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    def function_shape_set(self, shape: str):
        self._p.write_scpi(f'ARB:FUNCTION:SHAPE {shape}')

    def function_shape_query(self) -> str:  # Added: Missing query method
        return self._p.query_scpi('ARB:FUNCTION:SHAPE?')

    def function_type_set(self, typ: str):
        self._p.write_scpi(f'ARB:FUNCTION:TYPE {typ}')

    def function_type_query(self) -> str:  # Added: Missing query method
        return self._p.query_scpi('ARB:FUNCTION:TYPE?')

    # UDEFined list helpers
    def udef_count_set(self, steps: int):
        self._p.write_scpi(f'ARB:UDEFined:COUNt {int(steps)}')

    def udef_count_query(self) -> int:  # Added: Missing query method
        return parse_int(self._p.query_scpi('ARB:UDEFined:COUNt?'))

    def udef_level_set(self, step: int, level: Number):
        self._p.write_scpi(f'ARB:UDEFined:LEVel {int(step)},{float(level)}')

    def udef_level_query(self, step: int) -> float:  # Added: Missing query method
        return parse_float(self._p.query_scpi(f'ARB:UDEFined:LEVel? {int(step)}'))

    def udef_dwell_set(self, step: int, seconds: Number):
        self._p.write_scpi(f'ARB:UDEFined:DWELl {int(step)},{float(seconds)}')

    def udef_dwell_query(self, step: int) -> float:  # Added: Missing query method
        return parse_float(self._p.query_scpi(f'ARB:UDEFined:DWELl? {int(step)}'))

    def udef_slew_set(self, step: int, slew_val: Number):
        self._p.write_scpi(f'ARB:UDEFined:SLEW {int(step)},{float(slew_val)}')

    def udef_slew_query(self, step: int) -> float:  # Added: Missing query method
        return parse_float(self._p.query_scpi(f'ARB:UDEFined:SLEW? {int(step)}'))

    def count_set(self, cnt: int):
        self._p.write_scpi(f'ARB:COUNT {int(cnt)}')

    def count_query(self) -> int:  # Added: Missing query method
        return parse_int(self._p.query_scpi('ARB:COUNT?'))

    def terminate_last_set(self, last_state: int):
        self._p.write_scpi(f'ARB:TERMinate:LAST {int(last_state)}')

    def terminate_last_query(self) -> int:  # Added: Missing query method
        return parse_int(self._p.query_scpi('ARB:TERMinate:LAST?'))

    def save(self, index: int):
        self._p.write_scpi(f'ARB:SAVE {int(index)}')

    def recall(self, index: int):
        self._p.write_scpi(f'ARB:RECall {int(index)}')

    def init(self):
        self._p.write_scpi('INITiate:ARB')

    def trigger(self):
        self._p.write_scpi('TRIGger:ARB')

    def pause_set(self, enable: BoolLike):
        self._p.write_scpi(f'ARB:PAUSe:STATe {1 if enable else 0}')

    def pause_query(self) -> bool:  # Added: Missing query method
        return parse_bool(self._p.query_scpi('ARB:PAUSe:STATe?'))

    def abort(self):
        self._p.write_scpi('ABORt:ARB')

    def state_query(self) -> str:
        """Return raw execution status; do not infer completion or output state.

        Guide p.268 indexes ARB:EXE:STATe?; response codes are not yet qualified.
        """
        response = self._p.query_scpi('ARB:EXE:STAT?').strip()
        if not response:
            raise ResponseParseError('empty ARB execution status', raw=response)
        return response

