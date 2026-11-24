from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.scpi.parsers import parse_bool, parse_int
from ..base import  BaseInstrument, BoolLike, Number
# -------------------------
# Configurable IO Subsystem (IO)
# -------------------------
class IOConfigSubsystem:
    """General purpose IO configuration (IO:SELECT, IO:DIRECTION, PWM, etc.)."""
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    def select(self, idx: int):
        self._p.write_scpi(f'IO:SELect {int(idx)}')

    def select_query(self) -> int:
        return parse_int(self._p.query_scpi('IO:SELect?'))

    @staticmethod
    def _pin_index(pin) -> int:
        if isinstance(pin, str) and pin in tuple(str(i) for i in range(7)):
            pin = int(pin)
        if type(pin) is not int or not 0 <= pin <= 6:
            raise ConfigurationError("one protocol pin index in 0..6 is required")
        return pin

    def direction_set(self, pin_list: int | str, dir_mask: BoolLike | str):
        """Set direction: 0/OUT = output, 1/IN = input."""
        pin = self._pin_index(pin_list)
        if isinstance(dir_mask, str) and dir_mask.upper() in ("OUT", "IN"):
            direction = int(dir_mask.upper() == "IN")
        elif type(dir_mask) in (bool, int) and dir_mask in (0, 1):
            direction = int(dir_mask)
        else:
            raise ConfigurationError("direction must be OUT/0 or IN/1")
        self._p.write_scpi(f"IO:DIRE {pin},{direction}")

    def direction_query(self, pin_list: int | str) -> bool:
        """Return True for input and False for output; reject unknown replies."""
        pin = self._pin_index(pin_list)
        raw = self._p.query_scpi(f"IO:DIRE? {pin}").strip().upper()
        if raw in ("0", "OUT"):
            return False
        if raw in ("1", "IN"):
            return True
        raise ResponseParseError("invalid digital direction reply", raw=raw)

    def pwm_enable(self, ch: int, enable: BoolLike):
        self._p.write_scpi(f'IO:PWM:ENABle {int(ch)},{1 if enable else 0}')

    def pwm_freq_set(self, ch: int, freq: Number):
        self._p.write_scpi(f'IO:PWM:FREQuency {int(ch)},{float(freq)}')

    def pwm_duty_set(self, ch: int, duty_percent: int):
        self._p.write_scpi(f'IO:PWM:DUTY {int(ch)},{int(duty_percent)}')
