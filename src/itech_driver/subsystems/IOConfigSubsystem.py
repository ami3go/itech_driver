import math
from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.scpi.parsers import parse_bool, parse_int, parse_float
from ..base import  BaseInstrument, BoolLike, Number
# -------------------------
# Configurable IO Subsystem (IO)
# -------------------------
class IOConfigSubsystem:
    """General purpose IO configuration (IO:SELECT, IO:DIRECTION, PWM, etc.)."""
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    def select(self, idx: int):
        self._p.write_scpi(f'IO:SELect {self._pin_index(idx)}')

    def select_query(self) -> int:
        raw = self._p.query_scpi('IO:SELect?')
        value = parse_int(raw)
        if not 0 <= value <= 6:
            raise ResponseParseError('invalid selected pin index', raw=raw)
        return value

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
        pin = self._pin_index(ch)
        if type(enable) not in (bool, int) or enable not in (0, 1):
            raise ConfigurationError("PWM enable must be bool or 0/1")
        self._p.write_scpi(f'IO:PWM:ENABle {pin},{int(enable)}')

    def pwm_freq_set(self, ch: int, freq: Number):
        pin = self._pin_index(ch)
        if isinstance(freq, bool) or not isinstance(freq, (int, float)) or not math.isfinite(freq) or not 2 <= freq <= 21000:
            raise ConfigurationError("PWM frequency must be in 2..21000 Hz")
        self._p.write_scpi(f'IO:PWM:FREQuency {pin},{freq}')

    def pwm_duty_set(self, ch: int, duty_percent: int):
        pin = self._pin_index(ch)
        if type(duty_percent) is not int or not 1 <= duty_percent <= 100:
            raise ConfigurationError("PWM duty must be an integer in 1..100 percent")
        self._p.write_scpi(f'IO:PWM:DUTY {pin},{duty_percent}')

    _PIN_FUNCTIONS = (
        ("PSCL",), ("PSST",), ("OFFS",), ("EXTT", "TOUT"),
        ("INHLIV", "INHLAT"), ("SYON",), ("SYOFF",),
    )
    _COMMON_FUNCTIONS = ("IORD", "IOWR", "PWM")
    _FUNCTION_ALIASES = {
        "PSCLEAR":"PSCL", "PSCL":"PSCL", "PSSTA":"PSST", "PSST":"PSST",
        "OFFSTA":"OFFS", "OFFS":"OFFS", "EXTTRIG":"EXTT", "EXTTRI":"EXTT",
        "EXTT":"EXTT", "TOUT":"TOUT", "INHLIV":"INHLIV", "INHLAT":"INHLAT",
        "SYON":"SYON", "SYOFF":"SYOFF", "IORD":"IORD", "IOWR":"IOWR", "PWM":"PWM",
    }

    def reverse_set(self, pin, enabled):
        pin = self._pin_index(pin)
        if type(enabled) not in (bool,int) or enabled not in (0,1):
            raise ConfigurationError("reverse state must be bool or 0/1")
        self._p.write_scpi(f"IO:REVE {pin},{int(enabled)}")

    def reverse_query(self, pin):
        return parse_bool(self._p.query_scpi(f"IO:REVE? {self._pin_index(pin)}"))

    def pwm_enable_query(self, pin):
        return parse_bool(self._p.query_scpi(f"IO:PWM? {self._pin_index(pin)}"))

    def _pin_numeric_query(self, header, pin, bound=None):
        pin = self._pin_index(pin)
        if bound is not None and bound not in ("MIN","MAX","DEF"):
            raise ConfigurationError("invalid query bound")
        suffix = "" if bound is None else ","+bound
        return parse_float(self._p.query_scpi(f"{header}? {pin}{suffix}"))

    def pwm_freq_query(self,pin,*,bound=None):
        return self._pin_numeric_query("IO:PWM:FREQ",pin,bound)

    def pwm_duty_query(self,pin):
        raw = self._p.query_scpi(f"IO:PWM:DUTY? {self._pin_index(pin)}")
        duty = parse_int(raw)
        if not 0 <= duty <= 100:
            raise ResponseParseError("invalid duty cycle",raw=raw)
        return duty

    def pulse_width_query(self,pin,*,bound=None):
        return self._pin_numeric_query("IO:PULS:WIDT",pin,bound)

    def pulse_width_set(self,pin,seconds):
        pin = self._pin_index(pin)
        if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or seconds < 0:
            raise ConfigurationError("pulse width must be finite nonnegative seconds")
        with self._p.session.operation_lock():
            lo = self.pulse_width_query(pin,bound="MIN")
            hi = self.pulse_width_query(pin,bound="MAX")
            if not 0 <= lo <= seconds <= hi:
                raise ConfigurationError("pulse width outside reported range")
            self._p.write_scpi(f"IO:PULS:WIDT {pin},{seconds}")

    def _function_token(self,pin,function):
        token = self._FUNCTION_ALIASES.get(function.upper()) if isinstance(function,str) else None
        if token not in self._COMMON_FUNCTIONS + self._PIN_FUNCTIONS[pin]:
            raise ConfigurationError("function unsupported on selected pin")
        return token

    def pin_function_set(self,pin,function):
        pin = self._pin_index(pin)
        token = self._function_token(pin,function)
        # Use guide long forms for pin-specific tokens.
        wire = {"PSCL":"PSClear","PSST":"PSSTa","OFFS":"OFFSta","EXTT":"EXTTrig"}.get(token,token)
        self._p.write_scpi(f"IO:TYPE {pin},{wire}")

    def pin_function_query(self,pin):
        pin = self._pin_index(pin)
        raw = self._p.query_scpi(f"IO:TYPE? {pin}")
        try:
            return self._function_token(pin,raw.strip())
        except ConfigurationError as exc:
            raise ResponseParseError("invalid pin function response",raw=raw) from exc

    def _trigger_enum(self,header,value,allowed):
        token = value.upper() if isinstance(value,str) else None
        if token not in allowed:
            raise ConfigurationError("unsupported pin-4 trigger setting")
        self._p.write_scpi(f"{header} {token}")

    def _trigger_query(self,header,allowed):
        raw = self._p.query_scpi(header+"?").strip().upper()
        if raw not in allowed:
            raise ResponseParseError("invalid pin-4 trigger response",raw=raw)
        return raw

    def trigger_type_set(self,value):
        self._trigger_enum("IO:TRIG:TYPE",value,("TIN","TOUT"))

    def trigger_type_query(self):
        return self._trigger_query("IO:TRIG:TYPE",("TIN","TOUT"))

    def trigger_source_set(self,value):
        self._trigger_enum("IO:TRIG:SOUR",value,("METER","DLOG","LIST"))

    def trigger_source_query(self):
        return self._trigger_query("IO:TRIG:SOUR",("METER","DLOG","LIST"))

    def output_level_set(self,pin,high):
        pin = self._pin_index(pin)
        if type(high) not in (bool,int) or high not in (0,1):
            raise ConfigurationError("output level must be bool or 0/1")
        self._p.write_scpi(f"IO:OUTP:LEV {pin},{int(high)}")

    def _level_query(self,header,pin):
        raw = self._p.query_scpi(f"{header}? {self._pin_index(pin)}").strip().upper()
        if raw in ("0","LOW"):
            return False
        if raw in ("1","HIGH"):
            return True
        raise ResponseParseError("invalid digital level response",raw=raw)

    def output_level_query(self,pin):
        return self._level_query("IO:OUTP:LEV",pin)

    def input_level_query(self,pin):
        return self._level_query("IO:INP:LEV",pin)
