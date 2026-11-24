import math
import warnings
from scpi_driver_core import ConfigurationError, IdentityError, ResponseParseError, UnsupportedOperationError
from scpi_driver_core.scpi.parsers import parse_bool, parse_float
from ..base import  BaseInstrument, BoolLike, Number
from ..capabilities import ELECTRICAL_COMMANDS, Range, effective_command_range
from ..utils.validation import validate_channel, nonnegative_number, strict_bool
# -------------------------
# Source Subsystem (SOURce)
# -------------------------
class SourceSubsystem:
    """Source controls: mode, voltage/current setpoints, protections, etc."""
    def __init__(self, parent: BaseInstrument):
        self._p = parent

    _FUNCTIONS = {"VOLT": "VOLT", "VOLTAGE": "VOLT", "CURR": "CURR", "CURRENT": "CURR"}
    _MODES = {"FIX": "FIX", "FIXED": "FIX", "LIST": "LIST", "BATT": "BATT", "BATTERY": "BATT"}

    @staticmethod
    def _enum_arg(value, allowed):
        token = allowed.get(value.upper()) if isinstance(value, str) else None
        if token is None:
            raise ConfigurationError(f"unsupported source mode: {value!r}")
        return token

    def _enum_query(self, header, allowed):
        raw = self._p.query_scpi(f"{header}?")
        try:
            return self._enum_arg(raw.strip(), allowed)
        except ConfigurationError as exc:
            raise ResponseParseError("invalid source mode response", raw=raw) from exc

    def function_set(self, mode: str):
        """Select CV or CC priority, not a measurement of actual regulation mode."""
        self._p.write_scpi(f"SOUR:FUNC {self._enum_arg(mode, self._FUNCTIONS)}")

    def function_query(self) -> str:
        return self._enum_query("SOUR:FUNC", self._FUNCTIONS)

    def function_mode_set(self, mode: str):
        """Select fixed, list, or battery operation. Does not initiate or trigger."""
        self._p.write_scpi(f"SOUR:FUNC:MODE {self._enum_arg(mode, self._MODES)}")

    def function_mode_query(self) -> str:
        return self._enum_query("SOUR:FUNC:MODE", self._MODES)

    @staticmethod
    def _check_channel(channel: int) -> None:
        validate_channel(channel, 1)

    @staticmethod
    def _check_setpoint(value: Number) -> None:
        nonnegative_number(value, "setpoint")

    # Voltage / Current setpoints
    def voltage_set(self, value: Number, channel: int = 1):
        self._check_channel(channel)
        self._check_setpoint(value)
        self._limit_set('SOUR:VOLT', value)

    def voltage_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return parse_float(self._p.query_scpi('SOUR:VOLT?'))

    def current_set(self, value: Number, channel: int = 1):
        self._check_channel(channel)
        self._check_setpoint(value)
        self._limit_set('SOUR:CURR', value)

    def current_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return parse_float(self._p.query_scpi('SOUR:CURR?'))

    # Protections
    def ovp_set(self, value: Number, channel: int = 1):
        self._check_channel(channel)
        self._check_setpoint(value)
        self._p.write_scpi(f'SOUR:VOLT:OVER:PROT:LEV {value}')

    def ovp_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return parse_float(self._p.query_scpi(f'SOUR:VOLT:OVER:PROT:LEV?'))

    def ovp_enable(self, enable: BoolLike, channel: int = 1):
        self._check_channel(channel)
        enable = strict_bool(enable, "enable")
        self._p.write_scpi(f'SOUR:VOLT:OVER:PROT:STAT {1 if enable else 0}')

    def ovp_enable_query(self, channel: int = 1) -> bool:  # Added: Missing query method
        self._check_channel(channel)
        return parse_bool(self._p.query_scpi(f'SOUR:VOLT:OVER:PROT:STAT?'))

    def ocp_set(self, value: Number, channel: int = 1):
        self._check_channel(channel)
        self._check_setpoint(value)
        self._p.write_scpi(f'SOUR:CURR:OVER:PROT:LEV {value}')

    def ocp_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return parse_float(self._p.query_scpi(f'SOUR:CURR:OVER:PROT:LEV?'))

    def ocp_enable(self, enable: BoolLike, channel: int = 1):
        self._check_channel(channel)
        enable = strict_bool(enable, "enable")
        self._p.write_scpi(f'SOUR:CURR:OVER:PROT:STAT {1 if enable else 0}')

    def ocp_enable_query(self, channel: int = 1) -> bool:  # Added: Missing query method
        self._check_channel(channel)
        return parse_bool(self._p.query_scpi(f'SOUR:CURR:OVER:PROT:STAT?'))

    def opp_threshold_set(self, value: Number, channel: int = 1):
        self._check_channel(channel)
        self._check_setpoint(value)
        self._p.write_scpi(f'SOUR:POW:OVER:PROT:LEV {value}')

    def opp_threshold_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return parse_float(self._p.query_scpi('SOUR:POW:OVER:PROT:LEV?'))

    def opp_enable(self, enable: BoolLike, channel: int = 1):
        self._check_channel(channel)
        enable = strict_bool(enable, "enable")
        self._p.write_scpi(f'SOUR:POW:OVER:PROT:STAT {1 if enable else 0}')

    def opp_enable_query(self, channel: int = 1) -> bool:
        self._check_channel(channel)
        return parse_bool(self._p.query_scpi('SOUR:POW:OVER:PROT:STAT?'))

    def output_power_limit_set(self, value: Number, channel: int = 1):
        """Set the programmed power limit, not the OPP trip threshold."""
        self._check_channel(channel)
        self._limit_set('SOUR:POW:LIM', value)

    def output_power_limit_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return self._limit_query('SOUR:POW:LIM')

    def _limit_query(self, header, bound=None):
        if bound is not None and bound not in ("MIN", "MAX", "DEF"):
            raise ConfigurationError("bound must be MIN, MAX, DEF or None")
        suffix = "" if bound is None else " " + bound
        return parse_float(self._p.query_scpi(header + "?" + suffix))

    def _limit_set(self, header, value):
        self._check_setpoint(value)
        with self._p.session.operation_lock():
            self._p._assert_write_authorized()
            descriptor = None
            if header in ELECTRICAL_COMMANDS:
                descriptor = self._p.model_descriptor(refresh=False)
                if descriptor is None:
                    raise IdentityError("recognized rated ITECH model required for electrical setting")
            minimum = self._limit_query(header, "MIN")
            maximum = self._limit_query(header, "MAX")
            if not 0 <= minimum <= maximum:
                raise ConfigurationError("invalid reported instrument range")
            permitted = Range(minimum, maximum)
            if descriptor is not None:
                permitted = effective_command_range(
                    descriptor, header, permitted, self._p.application_limits
                )
            permitted.validate(value)
            self._p.write_scpi(f"{header} {value}")

    def voltage_limit_set(self, value: Number, channel: int = 1):
        self._check_channel(channel)
        self._limit_set("SOUR:VOLT:LIM", value)

    def voltage_limit_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query("SOUR:VOLT:LIM", bound)

    def current_limit_set(self, value: Number, channel: int = 1):
        self._check_channel(channel)
        self._limit_set("SOUR:CURR:LIM", value)

    def current_limit_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query("SOUR:CURR:LIM", bound)

    def programmed_power_limit_set(self, value: Number, channel: int = 1):
        self._check_channel(channel)
        self._limit_set("SOUR:POW:LIM", value)

    def programmed_power_limit_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query("SOUR:POW:LIM", bound)

    # Retain historical behavior explicitly during migration; never silently
    # turn an existing OPP threshold operation into a different setting.
    def power_limit_set(self, value: Number, channel: int = 1):
        warnings.warn("power_limit_set historically sets OPP; use opp_threshold_set "
                      "or output_power_limit_set", DeprecationWarning, stacklevel=2)
        return self.opp_threshold_set(value, channel)

    def power_limit_query(self, channel: int = 1) -> float:
        warnings.warn("power_limit_query historically reads OPP; use opp_threshold_query "
                      "or output_power_limit_query", DeprecationWarning, stacklevel=2)
        return self.opp_threshold_query(channel)

    def power_limit_enable(self, enable: BoolLike, channel: int = 1):
        warnings.warn("power_limit_enable historically enables OPP; use opp_enable",
                      DeprecationWarning, stacklevel=2)
        return self.opp_enable(enable, channel)

    def power_limit_enable_query(self, channel: int = 1) -> bool:
        warnings.warn("power_limit_enable_query historically reads OPP; use opp_enable_query",
                      DeprecationWarning, stacklevel=2)
        return self.opp_enable_query(channel)

    # Remote sense enable
    def remote_sense_set(self, enable: BoolLike, channel: int = 1):
        """Select remote sense only after independently verifying safe wiring.

        Do not use this operation as evidence that the physical wiring is valid.
        """
        self._check_channel(channel)
        enable = strict_bool(enable, "enable")
        self._p.write_scpi(f'SOUR:REM:SENS:STAT {1 if enable else 0}')

    def remote_sense_query(self, channel: int = 1) -> bool:
        self._check_channel(channel)
        # The available IT-M3900D guide index establishes the setter only.
        # Do not send an unverified readback header or infer state from a write.
        raise UnsupportedOperationError("IT-M3900D remote sense query not yet guide-qualified")

    # Advanced: transient / dynamic function interface
    def transient_mode_set(self, mode: str):
        self.function_mode_set(mode)

    def transient_mode_query(self) -> str:
        return self.function_mode_query()

    def ovp_delay_set(self, seconds: Number, channel: int = 1):
        self._check_channel(channel)
        self._limit_set("SOUR:VOLT:OVER:PROT:DEL", seconds)

    def ovp_delay_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query("SOUR:VOLT:OVER:PROT:DEL", bound)

    def ocp_delay_set(self, seconds: Number, channel: int = 1):
        self._check_channel(channel)
        self._limit_set("SOUR:CURR:OVER:PROT:DEL", seconds)

    def ocp_delay_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query("SOUR:CURR:OVER:PROT:DEL", bound)

    def opp_delay_set(self, seconds: Number, channel: int = 1):
        self._check_channel(channel)
        self._limit_set("SOUR:POW:OVER:PROT:DEL", seconds)

    def opp_delay_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query("SOUR:POW:OVER:PROT:DEL", bound)

    def uvp_delay_set(self, seconds: Number, channel: int = 1):
        self._check_channel(channel)
        self._limit_set("SOUR:VOLT:UND:PROT:DEL", seconds)

    def uvp_delay_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query("SOUR:VOLT:UND:PROT:DEL", bound)

    def ucp_delay_set(self, seconds: Number, channel: int = 1):
        self._check_channel(channel)
        self._limit_set("SOUR:CURR:UND:PROT:DEL", seconds)

    def ucp_delay_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query("SOUR:CURR:UND:PROT:DEL", bound)

    def uvp_warmup_set(self, seconds: Number, channel: int = 1):
        self._check_channel(channel)
        self._limit_set("SOUR:VOLT:UND:PROT:WARM", seconds)

    def uvp_warmup_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query("SOUR:VOLT:UND:PROT:WARM", bound)

    def ucp_warmup_set(self, seconds: Number, channel: int = 1):
        self._check_channel(channel)
        self._limit_set("SOUR:CURR:UND:PROT:WARM", seconds)

    def ucp_warmup_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query("SOUR:CURR:UND:PROT:WARM", bound)

    def uvp_set(self, value: Number, channel: int = 1):
        self._check_channel(channel)
        self._check_setpoint(value)
        self._p.write_scpi(f"SOUR:VOLT:UND:PROT:LEV {value}")

    def uvp_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return parse_float(self._p.query_scpi("SOUR:VOLT:UND:PROT:LEV?"))

    def uvp_enable(self, enable: BoolLike, channel: int = 1):
        self._check_channel(channel)
        enable = strict_bool(enable, "enable")
        self._p.write_scpi(f"SOUR:VOLT:UND:PROT:STAT {int(enable)}")

    def uvp_enable_query(self, channel: int = 1) -> bool:
        self._check_channel(channel)
        return parse_bool(self._p.query_scpi("SOUR:VOLT:UND:PROT:STAT?"))

    def ucp_set(self, value: Number, channel: int = 1):
        self._check_channel(channel)
        self._check_setpoint(value)
        self._p.write_scpi(f"SOUR:CURR:UND:PROT:LEV {value}")

    def ucp_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return parse_float(self._p.query_scpi("SOUR:CURR:UND:PROT:LEV?"))

    def ucp_enable(self, enable: BoolLike, channel: int = 1):
        self._check_channel(channel)
        enable = strict_bool(enable, "enable")
        self._p.write_scpi(f"SOUR:CURR:UND:PROT:STAT {int(enable)}")

    def ucp_enable_query(self, channel: int = 1) -> bool:
        self._check_channel(channel)
        return parse_bool(self._p.query_scpi("SOUR:CURR:UND:PROT:STAT?"))

    def voltage_rise_time_set(self, seconds: Number, channel: int = 1):
        """Set duration in seconds, not a slew rate in units/s."""
        self._check_channel(channel)
        self._limit_set("SOUR:VOLT:SLEW:POS", seconds)

    def voltage_rise_time_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query("SOUR:VOLT:SLEW:POS", bound)

    def voltage_fall_time_set(self, seconds: Number, channel: int = 1):
        """Set duration in seconds, not a slew rate in units/s."""
        self._check_channel(channel)
        self._limit_set("SOUR:VOLT:SLEW:NEG", seconds)

    def voltage_fall_time_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query("SOUR:VOLT:SLEW:NEG", bound)

    def voltage_both_time_set(self, seconds: Number, channel: int = 1):
        """Set duration in seconds, not a slew rate in units/s."""
        self._check_channel(channel)
        self._limit_set("SOUR:VOLT:SLEW:BOTH", seconds)

    def voltage_both_time_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query("SOUR:VOLT:SLEW:BOTH", bound)

    def current_rise_time_set(self, seconds: Number, channel: int = 1):
        """Set duration in seconds, not a slew rate in units/s."""
        self._check_channel(channel)
        self._limit_set("SOUR:CURR:SLEW:POS", seconds)

    def current_rise_time_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query("SOUR:CURR:SLEW:POS", bound)

    def current_fall_time_set(self, seconds: Number, channel: int = 1):
        """Set duration in seconds, not a slew rate in units/s."""
        self._check_channel(channel)
        self._limit_set("SOUR:CURR:SLEW:NEG", seconds)

    def current_fall_time_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query("SOUR:CURR:SLEW:NEG", bound)

    def current_both_time_set(self, seconds: Number, channel: int = 1):
        """Set duration in seconds, not a slew rate in units/s."""
        self._check_channel(channel)
        self._limit_set("SOUR:CURR:SLEW:BOTH", seconds)

    def current_both_time_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query("SOUR:CURR:SLEW:BOTH", bound)

    def cv_loop_speed_set(self, speed: str):
        self._p.write_scpi(f"SOUR:CV:PRI {self._enum_arg(speed, {'HIGH': 'HIGH', 'LOW': 'LOW'})}")

    def cv_loop_speed_query(self) -> str:
        return self._enum_query("SOUR:CV:PRI", {"HIGH": "HIGH", "LOW": "LOW"})

    def cc_loop_speed_set(self, speed: str):
        self._p.write_scpi(f"SOUR:CC:PRI {self._enum_arg(speed, {'HIGH': 'HIGH', 'LOW': 'LOW'})}")

    def cc_loop_speed_query(self) -> str:
        return self._enum_query("SOUR:CC:PRI", {"HIGH": "HIGH", "LOW": "LOW"})

    def external_programming_query(self) -> bool:
        return parse_bool(self._p.query_scpi("SOUR:EXT:PROG?"))

    def external_programming_set(self, enabled: BoolLike, *, wiring_confirmed=False,
                                 deenergized_confirmed=False, option_confirmed=False):
        """Change analog control only with independently confirmed safe conditions."""
        if type(enabled) not in (bool,int) or enabled not in (0,1):
            raise ConfigurationError("external programming state must be bool or 0/1")
        if not all(flag is True for flag in (wiring_confirmed,deenergized_confirmed,option_confirmed)):
            raise ConfigurationError("confirm analog option, wiring and de-energized output")
        with self._p.session.operation_lock():
            if parse_bool(self._p.query_scpi("OUTP:STAT?")):
                raise ConfigurationError("programmed output must be disabled")
            self._p.write_scpi(f"SOUR:EXT:PROG {int(enabled)}")

    @staticmethod
    def _analog_channel(channel):
        if type(channel) is not int or channel not in (1,2,3):
            raise ConfigurationError("external analog channel must be 1, 2 or 3")
        return channel

    def external_coefficient_query(self, channel: int, coefficient: str) -> float:
        channel = self._analog_channel(channel)
        if coefficient not in ("MX","MB"):
            raise ConfigurationError("coefficient must be MX or MB")
        raw = self._p.query_scpi(f"SOUR:EXT:PROG:CHAN:{coefficient}? {channel}")
        value = parse_float(raw)
        if not -9000 <= value <= 9000:
            raise ResponseParseError("external coefficient outside documented bounds",raw=raw)
        return value

    def external_coefficient_set(self, channel: int, coefficient: str, value: Number, *,
                                 option_confirmed=False, deenergized_confirmed=False):
        channel = self._analog_channel(channel)
        if coefficient not in ("MX","MB"):
            raise ConfigurationError("coefficient must be MX or MB")
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not -9000 <= value <= 9000:
            raise ConfigurationError("external coefficient must be finite in -9000..9000")
        if option_confirmed is not True or deenergized_confirmed is not True:
            raise ConfigurationError("confirm analog option and de-energized output")
        with self._p.session.operation_lock():
            if parse_bool(self._p.query_scpi("OUTP:STAT?")) or self.external_programming_query():
                raise ConfigurationError("disable output and external control before changing coefficients")
            self._p.write_scpi(f"SOUR:EXT:PROG:CHAN:{coefficient} {channel},{value}")

    def resistance_query(self, *, bound=None) -> float:
        """Query programmed internal resistance in ohms (CV priority only)."""
        with self._p.session.operation_lock():
            if self.function_query() != "VOLT":
                raise ConfigurationError("internal resistance requires CV priority")
            return self._limit_query("SOUR:RES",bound)

    def resistance_set(self, ohms: Number):
        """Set CV internal resistance using the device's reported range."""
        self._check_setpoint(ohms)
        with self._p.session.operation_lock():
            if self.function_query() != "VOLT":
                raise ConfigurationError("internal resistance requires CV priority")
            self._limit_set("SOUR:RES",ohms)
