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
        return int(self._p.query_scpi('IO:SELect?'))

    def direction_set(self, pin_list: str, dir_mask: BoolLike):
        # pin_list could be '1,2,3' or similar per manual
        self._p.write_scpi(f'IO:DIREction {pin_list},{1 if dir_mask else 0}')

    def direction_query(self, pin_list: str) -> bool:  # Added: Missing query method
        return bool(int(self._p.query_scpi(f'IO:DIREction? {pin_list}')))

    def pwm_enable(self, ch: int, enable: BoolLike):
        self._p.write_scpi(f'IO:PWM:ENABle {int(ch)},{1 if enable else 0}')

    def pwm_freq_set(self, ch: int, freq: Number):
        self._p.write_scpi(f'IO:PWM:FREQuency {int(ch)},{float(freq)}')

    def pwm_duty_set(self, ch: int, duty_percent: int):
        self._p.write_scpi(f'IO:PWM:DUTY {int(ch)},{int(duty_percent)}')