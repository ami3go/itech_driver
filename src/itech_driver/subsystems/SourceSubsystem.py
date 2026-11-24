from ..command_specs import execute, execute_parameterized, command_spec
import math
import warnings
from scpi_driver_core import ConfigurationError, IdentityError, ResponseParseError, UnsupportedOperationError
from scpi_driver_core.scpi.parsers import parse_bool, parse_float
from ..base import  BaseInstrument, BoolLike, Number
from ..capabilities import ELECTRICAL_COMMANDS, Range, effective_command_range
from ..utils.validation import validate_channel, nonnegative_number, strict_bool
from ..protection import PROTECTION_THRESHOLDS, ProtectionThresholdQualification, set_protection_threshold
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
        execute_parameterized(self._p, "SourceSubsystem.function_set", self._enum_arg(mode, self._FUNCTIONS))

    def function_query(self) -> str:
        return self._enum_query(command_spec("SourceSubsystem.function_query").header, self._FUNCTIONS)

    def function_mode_set(self, mode: str):
        """Select fixed, list, or battery operation. Does not initiate or trigger."""
        execute_parameterized(self._p, "SourceSubsystem.function_mode_set", self._enum_arg(mode, self._MODES))

    def function_mode_query(self) -> str:
        return self._enum_query(command_spec("SourceSubsystem.function_mode_query").header, self._MODES)

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
        self._limit_set(command_spec("SourceSubsystem.voltage_set").header, value)

    def voltage_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return execute(self._p, "SourceSubsystem.voltage_query")

    def current_set(self, value: Number, channel: int = 1):
        self._check_channel(channel)
        self._check_setpoint(value)
        self._limit_set(command_spec("SourceSubsystem.current_set").header, value)

    def current_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return execute(self._p, "SourceSubsystem.current_query")

    # Protections
    def ovp_set(self, value: Number, channel: int = 1, *, qualification: ProtectionThresholdQualification | None = None):
        self._check_channel(channel)
        self._check_setpoint(value)
        set_protection_threshold(self._p, "ovp", value, qualification)

    def ovp_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return execute(self._p, "SourceSubsystem.ovp_query")

    def ovp_enable(self, enable: BoolLike, channel: int = 1):
        self._check_channel(channel)
        enable = strict_bool(enable, "enable")
        execute_parameterized(self._p, "SourceSubsystem.ovp_enable", enable)

    def ovp_enable_query(self, channel: int = 1) -> bool:  # Added: Missing query method
        self._check_channel(channel)
        return execute(self._p, "SourceSubsystem.ovp_enable_query")

    def ocp_set(self, value: Number, channel: int = 1, *, qualification: ProtectionThresholdQualification | None = None):
        self._check_channel(channel)
        self._check_setpoint(value)
        set_protection_threshold(self._p, "ocp", value, qualification)

    def ocp_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return execute(self._p, "SourceSubsystem.ocp_query")

    def ocp_enable(self, enable: BoolLike, channel: int = 1):
        self._check_channel(channel)
        enable = strict_bool(enable, "enable")
        execute_parameterized(self._p, "SourceSubsystem.ocp_enable", enable)

    def ocp_enable_query(self, channel: int = 1) -> bool:  # Added: Missing query method
        self._check_channel(channel)
        return execute(self._p, "SourceSubsystem.ocp_enable_query")

    def opp_threshold_set(self, value: Number, channel: int = 1, *, qualification: ProtectionThresholdQualification | None = None):
        self._check_channel(channel)
        self._check_setpoint(value)
        set_protection_threshold(self._p, "opp", value, qualification)

    def opp_threshold_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return execute(self._p, "SourceSubsystem.opp_threshold_query")

    def opp_enable(self, enable: BoolLike, channel: int = 1):
        self._check_channel(channel)
        enable = strict_bool(enable, "enable")
        execute_parameterized(self._p, "SourceSubsystem.opp_enable", enable)

    def opp_enable_query(self, channel: int = 1) -> bool:
        self._check_channel(channel)
        return execute(self._p, "SourceSubsystem.opp_enable_query")

    def output_power_limit_set(self, value: Number, channel: int = 1):
        """Set the programmed power limit, not the OPP trip threshold."""
        self._check_channel(channel)
        self._limit_set(command_spec("SourceSubsystem.output_power_limit_set").header, value)

    def output_power_limit_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return self._limit_query(command_spec("SourceSubsystem.output_power_limit_query").header)

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
        self._limit_set(command_spec("SourceSubsystem.voltage_limit_set").header, value)

    def voltage_limit_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query(command_spec("SourceSubsystem.voltage_limit_query").header, bound)

    def current_limit_set(self, value: Number, channel: int = 1):
        self._check_channel(channel)
        self._limit_set(command_spec("SourceSubsystem.current_limit_set").header, value)

    def current_limit_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query(command_spec("SourceSubsystem.current_limit_query").header, bound)

    def programmed_power_limit_set(self, value: Number, channel: int = 1):
        self._check_channel(channel)
        self._limit_set(command_spec("SourceSubsystem.programmed_power_limit_set").header, value)

    def programmed_power_limit_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query(command_spec("SourceSubsystem.programmed_power_limit_query").header, bound)

    # Retain historical behavior explicitly during migration; never silently
    # turn an existing OPP threshold operation into a different setting.
    def power_limit_set(self, value: Number, channel: int = 1, *, qualification: ProtectionThresholdQualification | None = None):
        warnings.warn("power_limit_set historically sets OPP; use opp_threshold_set "
                      "or output_power_limit_set", DeprecationWarning, stacklevel=2)
        return self.opp_threshold_set(value, channel, qualification=qualification)

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
        execute_parameterized(self._p, "SourceSubsystem.remote_sense_set", enable)

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
        self._limit_set(command_spec("SourceSubsystem.ovp_delay_set").header, seconds)

    def ovp_delay_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query(command_spec("SourceSubsystem.ovp_delay_query").header, bound)

    def ocp_delay_set(self, seconds: Number, channel: int = 1):
        self._check_channel(channel)
        self._limit_set(command_spec("SourceSubsystem.ocp_delay_set").header, seconds)

    def ocp_delay_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query(command_spec("SourceSubsystem.ocp_delay_query").header, bound)

    def opp_delay_set(self, seconds: Number, channel: int = 1):
        self._check_channel(channel)
        self._limit_set(command_spec("SourceSubsystem.opp_delay_set").header, seconds)

    def opp_delay_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query(command_spec("SourceSubsystem.opp_delay_query").header, bound)

    def uvp_delay_set(self, seconds: Number, channel: int = 1):
        self._check_channel(channel)
        self._limit_set(command_spec("SourceSubsystem.uvp_delay_set").header, seconds)

    def uvp_delay_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query(command_spec("SourceSubsystem.uvp_delay_query").header, bound)

    def ucp_delay_set(self, seconds: Number, channel: int = 1):
        self._check_channel(channel)
        self._limit_set(command_spec("SourceSubsystem.ucp_delay_set").header, seconds)

    def ucp_delay_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query(command_spec("SourceSubsystem.ucp_delay_query").header, bound)

    def uvp_warmup_set(self, seconds: Number, channel: int = 1):
        self._check_channel(channel)
        self._limit_set(command_spec("SourceSubsystem.uvp_warmup_set").header, seconds)

    def uvp_warmup_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query(command_spec("SourceSubsystem.uvp_warmup_query").header, bound)

    def ucp_warmup_set(self, seconds: Number, channel: int = 1):
        self._check_channel(channel)
        self._limit_set(command_spec("SourceSubsystem.ucp_warmup_set").header, seconds)

    def ucp_warmup_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query(command_spec("SourceSubsystem.ucp_warmup_query").header, bound)

    def uvp_set(self, value: Number, channel: int = 1, *, qualification: ProtectionThresholdQualification | None = None):
        self._check_channel(channel)
        self._check_setpoint(value)
        set_protection_threshold(self._p, "uvp", value, qualification)

    def uvp_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return execute(self._p, "SourceSubsystem.uvp_query")

    def uvp_enable(self, enable: BoolLike, channel: int = 1):
        self._check_channel(channel)
        enable = strict_bool(enable, "enable")
        execute_parameterized(self._p, "SourceSubsystem.uvp_enable", enable)

    def uvp_enable_query(self, channel: int = 1) -> bool:
        self._check_channel(channel)
        return execute(self._p, "SourceSubsystem.uvp_enable_query")

    def ucp_set(self, value: Number, channel: int = 1, *, qualification: ProtectionThresholdQualification | None = None):
        self._check_channel(channel)
        self._check_setpoint(value)
        set_protection_threshold(self._p, "ucp", value, qualification)

    def ucp_query(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return execute(self._p, "SourceSubsystem.ucp_query")

    def ucp_enable(self, enable: BoolLike, channel: int = 1):
        self._check_channel(channel)
        enable = strict_bool(enable, "enable")
        execute_parameterized(self._p, "SourceSubsystem.ucp_enable", enable)

    def ucp_enable_query(self, channel: int = 1) -> bool:
        self._check_channel(channel)
        return execute(self._p, "SourceSubsystem.ucp_enable_query")

    def voltage_rise_time_set(self, seconds: Number, channel: int = 1):
        """Set duration in seconds, not a slew rate in units/s."""
        self._check_channel(channel)
        self._limit_set(command_spec("SourceSubsystem.voltage_rise_time_set").header, seconds)

    def voltage_rise_time_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query(command_spec("SourceSubsystem.voltage_rise_time_query").header, bound)

    def voltage_fall_time_set(self, seconds: Number, channel: int = 1):
        """Set duration in seconds, not a slew rate in units/s."""
        self._check_channel(channel)
        self._limit_set(command_spec("SourceSubsystem.voltage_fall_time_set").header, seconds)

    def voltage_fall_time_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query(command_spec("SourceSubsystem.voltage_fall_time_query").header, bound)

    def voltage_both_time_set(self, seconds: Number, channel: int = 1):
        """Set duration in seconds, not a slew rate in units/s."""
        self._check_channel(channel)
        self._limit_set(command_spec("SourceSubsystem.voltage_both_time_set").header, seconds)

    def voltage_both_time_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query(command_spec("SourceSubsystem.voltage_both_time_query").header, bound)

    def current_rise_time_set(self, seconds: Number, channel: int = 1):
        """Set duration in seconds, not a slew rate in units/s."""
        self._check_channel(channel)
        self._limit_set(command_spec("SourceSubsystem.current_rise_time_set").header, seconds)

    def current_rise_time_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query(command_spec("SourceSubsystem.current_rise_time_query").header, bound)

    def current_fall_time_set(self, seconds: Number, channel: int = 1):
        """Set duration in seconds, not a slew rate in units/s."""
        self._check_channel(channel)
        self._limit_set(command_spec("SourceSubsystem.current_fall_time_set").header, seconds)

    def current_fall_time_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query(command_spec("SourceSubsystem.current_fall_time_query").header, bound)

    def current_both_time_set(self, seconds: Number, channel: int = 1):
        """Set duration in seconds, not a slew rate in units/s."""
        self._check_channel(channel)
        self._limit_set(command_spec("SourceSubsystem.current_both_time_set").header, seconds)

    def current_both_time_query(self, channel: int = 1, *, bound=None) -> float:
        self._check_channel(channel)
        return self._limit_query(command_spec("SourceSubsystem.current_both_time_query").header, bound)

    def cv_loop_speed_set(self, speed: str):
        execute_parameterized(self._p, "SourceSubsystem.cv_loop_speed_set", self._enum_arg(speed, {"HIGH": "HIGH", "LOW": "LOW"}))

    def cv_loop_speed_query(self) -> str:
        return self._enum_query(command_spec("SourceSubsystem.cv_loop_speed_query").header, {"HIGH": "HIGH", "LOW": "LOW"})

    def cc_loop_speed_set(self, speed: str):
        execute_parameterized(self._p, "SourceSubsystem.cc_loop_speed_set", self._enum_arg(speed, {"HIGH": "HIGH", "LOW": "LOW"}))

    def cc_loop_speed_query(self) -> str:
        return self._enum_query(command_spec("SourceSubsystem.cc_loop_speed_query").header, {"HIGH": "HIGH", "LOW": "LOW"})

    def external_programming_query(self) -> bool:
        return execute(self._p, "SourceSubsystem.external_programming_query")

    def external_programming_set(self, enabled: BoolLike, *, wiring_confirmed=False,
                                 deenergized_confirmed=False, option_confirmed=False):
        """Change analog control only with independently confirmed safe conditions."""
        if type(enabled) not in (bool,int) or enabled not in (0,1):
            raise ConfigurationError("external programming state must be bool or 0/1")
        if not all(flag is True for flag in (wiring_confirmed,deenergized_confirmed,option_confirmed)):
            raise ConfigurationError("confirm analog option, wiring and de-energized output")
        with self._p.session.operation_lock():
            self._p._require_methods("OutputSubsystem.state_query")
            self._p._assert_write_authorized()
            if self._p.output.state_query():
                raise ConfigurationError("programmed output must be disabled")
            self._p.write_scpi(command_spec("SourceSubsystem.external_programming_set").header + f" {int(enabled)}")

    @staticmethod
    def _analog_channel(channel):
        if type(channel) is not int or channel not in (1,2,3):
            raise ConfigurationError("external analog channel must be 1, 2 or 3")
        return channel

    def external_coefficient_query(self, channel: int, coefficient: str) -> float:
        channel = self._analog_channel(channel)
        if coefficient not in ("MX","MB"):
            raise ConfigurationError("coefficient must be MX or MB")
        header = command_spec("SourceSubsystem.external_coefficient_query").header.format(coefficient=coefficient)
        raw = self._p.query_scpi(f"{header} {channel}")
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
            self._p._require_methods("OutputSubsystem.state_query", "SourceSubsystem.external_programming_query")
            self._p._assert_write_authorized()
            if self._p.output.state_query() or self.external_programming_query():
                raise ConfigurationError("disable output and external control before changing coefficients")
            header = command_spec("SourceSubsystem.external_coefficient_set").header.format(coefficient=coefficient)
            self._p.write_scpi(f"{header} {channel},{value}")

    def resistance_query(self, *, bound=None) -> float:
        """Query programmed internal resistance in ohms (CV priority only)."""
        with self._p.session.operation_lock():
            if self.function_query() != "VOLT":
                raise ConfigurationError("internal resistance requires CV priority")
            return self._limit_query(command_spec("SourceSubsystem.resistance_query").header,bound)

    def resistance_set(self, ohms: Number):
        """Set CV internal resistance using the device's reported range."""
        self._check_setpoint(ohms)
        with self._p.session.operation_lock():
            if self.function_query() != "VOLT":
                raise ConfigurationError("internal resistance requires CV priority")
            self._limit_set(command_spec("SourceSubsystem.resistance_set").header,ohms)
