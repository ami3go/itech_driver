from ..command_specs import execute, execute_parameterized, command_spec
from scpi_driver_core import ResponseParseError, UnsupportedOperationError
from scpi_driver_core.scpi.parsers import parse_bool, parse_float, parse_int
from ..base import  BaseInstrument, BoolLike, Number
from ..utils.validation import exact_integer, finite_number, strict_bool
from ..arb_integer_qualification import FAMILY_INTEGER_MAX, validate_arb_integer
# -------------------------
# ARB / List Subsystem (ARB)
# -------------------------
# Conservative IT-M3900D family LIST bounds, User Manual V2.6/5,2025,
# section 4.6.1 pp.58–59. Full command/firmware qualification remains separate.
# Zero repetition is deliberately not accepted: finite execution only.
_LIST_STEPS = FAMILY_INTEGER_MAX['udef_count_set']
_LIST_FILES = FAMILY_INTEGER_MAX['save']
_FINITE_REPEATS = FAMILY_INTEGER_MAX['count_set']


def _step(value):
    return exact_integer(value, minimum=1, maximum=_LIST_STEPS, name="LIST step")


def _slot(value):
    return exact_integer(value, minimum=1, maximum=_LIST_FILES, name="LIST file")


def _repeat(value):
    return exact_integer(value, minimum=1, maximum=_FINITE_REPEATS, name="finite repeat count")


class ArbSubsystem:
    """ARB / List / Sequence programming and execution."""
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    def function_shape_set(self, shape: str):
        execute_parameterized(self._p, "ArbSubsystem.function_shape_set", f'{shape}')

    def function_shape_query(self) -> str:  # Added: Missing query method
        return execute(self._p, "ArbSubsystem.function_shape_query")

    def function_type_set(self, typ: str):
        execute_parameterized(self._p, "ArbSubsystem.function_type_set", f'{typ}')

    def function_type_query(self) -> str:  # Added: Missing query method
        return execute(self._p, "ArbSubsystem.function_type_query")

    # UDEFined list helpers
    def udef_count_set(self, steps: int):
        execute_parameterized(self._p, "ArbSubsystem.udef_count_set", f'{validate_arb_integer(self._p, "udef_count_set", steps)}')

    def udef_count_query(self) -> int:  # Added: Missing query method
        return parse_int(execute(self._p, "ArbSubsystem.udef_count_query"))

    def udef_level_set(self, step: int, level: Number):
        execute_parameterized(self._p, "ArbSubsystem.udef_level_set", f'{validate_arb_integer(self._p, "udef_level_set", step)},{float(finite_number(level))}')

    def udef_level_query(self, step: int) -> float:  # Added: Missing query method
        return parse_float(execute_parameterized(self._p, "ArbSubsystem.udef_level_query", f'{validate_arb_integer(self._p, "udef_level_query", step)}'))

    def udef_dwell_set(self, step: int, seconds: Number):
        execute_parameterized(self._p, "ArbSubsystem.udef_dwell_set", f'{validate_arb_integer(self._p, "udef_dwell_set", step)},{float(finite_number(seconds))}')

    def udef_dwell_query(self, step: int) -> float:  # Added: Missing query method
        return parse_float(execute_parameterized(self._p, "ArbSubsystem.udef_dwell_query", f'{validate_arb_integer(self._p, "udef_dwell_query", step)}'))

    def udef_slew_set(self, step: int, slew_val: Number):
        execute_parameterized(self._p, "ArbSubsystem.udef_slew_set", f'{validate_arb_integer(self._p, "udef_slew_set", step)},{float(finite_number(slew_val))}')

    def udef_slew_query(self, step: int) -> float:  # Added: Missing query method
        return parse_float(execute_parameterized(self._p, "ArbSubsystem.udef_slew_query", f'{validate_arb_integer(self._p, "udef_slew_query", step)}'))

    def count_set(self, cnt: int):
        execute_parameterized(self._p, "ArbSubsystem.count_set", f'{validate_arb_integer(self._p, "count_set", cnt)}')

    def count_query(self) -> int:  # Added: Missing query method
        return parse_int(execute(self._p, "ArbSubsystem.count_query"))

    def terminate_last_set(self, last_state: int):
        """Unavailable until IT-M3900D termination modes are qualified."""
        raise UnsupportedOperationError(
            "ARB termination modes require IT-M3900D guide qualification")

    def terminate_last_query(self) -> int:
        """Do not interpret an unqualified discrete response as an integer."""
        raise UnsupportedOperationError(
            "ARB termination response requires IT-M3900D guide qualification")

    def save(self, index: int):
        execute_parameterized(self._p, "ArbSubsystem.save", f'{validate_arb_integer(self._p, "save", index)}')

    def recall(self, index: int):
        execute_parameterized(self._p, "ArbSubsystem.recall", f'{validate_arb_integer(self._p, "recall", index)}')

    def init(self):
        return self._p.initiate.arb()

    def trigger(self):
        execute(self._p, "ArbSubsystem.trigger")

    def pause_set(self, enable: BoolLike):
        execute_parameterized(self._p, "ArbSubsystem.pause_set", f'{1 if strict_bool(enable) else 0}')

    def pause_query(self) -> bool:  # Added: Missing query method
        return parse_bool(execute(self._p, "ArbSubsystem.pause_query"))

    def abort(self):
        return self._p.abort.arb()

    def state_query(self) -> str:
        """Return raw execution status; do not infer completion or output state.

        Guide p.268 indexes ARB:EXE:STATe?; response codes are not yet qualified.
        """
        response = execute(self._p, "ArbSubsystem.state_query").strip()
        if not response:
            raise ResponseParseError('empty ARB execution status', raw=response)
        return response

