"""Explicit model, firmware and interface evidence for typed subsystem methods."""
from dataclasses import dataclass
from functools import wraps
import inspect
from types import MappingProxyType
from typing import Mapping

from scpi_driver_core import ConfigurationError, UnsupportedOperationError
from .capabilities import CapabilityState, MODEL_DESCRIPTORS

METHOD_KEYS = frozenset((
    "AbortSubsystem.acquire",
    "AbortSubsystem.arb",
    "AbortSubsystem.dlog",
    "AbortSubsystem.elog",
    "ArbSubsystem.abort",
    "ArbSubsystem.count_query",
    "ArbSubsystem.count_set",
    "ArbSubsystem.function_shape_query",
    "ArbSubsystem.function_shape_set",
    "ArbSubsystem.function_type_query",
    "ArbSubsystem.function_type_set",
    "ArbSubsystem.init",
    "ArbSubsystem.pause_query",
    "ArbSubsystem.pause_set",
    "ArbSubsystem.recall",
    "ArbSubsystem.save",
    "ArbSubsystem.state_query",
    "ArbSubsystem.terminate_last_query",
    "ArbSubsystem.terminate_last_set",
    "ArbSubsystem.trigger",
    "ArbSubsystem.udef_count_query",
    "ArbSubsystem.udef_count_set",
    "ArbSubsystem.udef_dwell_query",
    "ArbSubsystem.udef_dwell_set",
    "ArbSubsystem.udef_level_query",
    "ArbSubsystem.udef_level_set",
    "ArbSubsystem.udef_slew_query",
    "ArbSubsystem.udef_slew_set",
    "BatterySubsystem.charge_current_query",
    "BatterySubsystem.charge_current_set",
    "BatterySubsystem.charge_voltage_query",
    "BatterySubsystem.charge_voltage_set",
    "BatterySubsystem.mode_query",
    "BatterySubsystem.mode_set",
    "BatterySubsystem.shutdown_capacity_query",
    "BatterySubsystem.shutdown_capacity_set",
    "BatterySubsystem.shutdown_current_query",
    "BatterySubsystem.shutdown_current_set",
    "BatterySubsystem.shutdown_time_query",
    "BatterySubsystem.shutdown_time_set",
    "BatterySubsystem.shutdown_voltage_query",
    "BatterySubsystem.shutdown_voltage_set",
    "BatterySubsystem.state_query",
    "BatterySubsystem.state_set",
    "FetchSubsystem.current_array_query",
    "FetchSubsystem.current_binary_array_query",
    "FetchSubsystem.current_high_query",
    "FetchSubsystem.current_low_query",
    "FetchSubsystem.current_max_query",
    "FetchSubsystem.current_min_query",
    "FetchSubsystem.current_query",
    "FetchSubsystem.power_array_query",
    "FetchSubsystem.power_binary_array_query",
    "FetchSubsystem.power_max_query",
    "FetchSubsystem.power_min_query",
    "FetchSubsystem.power_query",
    "FetchSubsystem.voltage_array_query",
    "FetchSubsystem.voltage_binary_array_query",
    "FetchSubsystem.voltage_high_query",
    "FetchSubsystem.voltage_low_query",
    "FetchSubsystem.voltage_max_query",
    "FetchSubsystem.voltage_min_query",
    "FetchSubsystem.voltage_query",
    "IEEE488.clear_status",
    "IEEE488.opc",
    "IEEE488.recall",
    "IEEE488.reset",
    "IEEE488.save",
    "IEEE488.self_test",
    "IEEE488.trigger",
    "IOConfigSubsystem.direction_query",
    "IOConfigSubsystem.direction_set",
    "IOConfigSubsystem.input_level_query",
    "IOConfigSubsystem.output_level_query",
    "IOConfigSubsystem.output_level_set",
    "IOConfigSubsystem.pin_function_query",
    "IOConfigSubsystem.pin_function_set",
    "IOConfigSubsystem.pulse_width_query",
    "IOConfigSubsystem.pulse_width_set",
    "IOConfigSubsystem.pwm_duty_query",
    "IOConfigSubsystem.pwm_duty_set",
    "IOConfigSubsystem.pwm_enable",
    "IOConfigSubsystem.pwm_enable_query",
    "IOConfigSubsystem.pwm_freq_query",
    "IOConfigSubsystem.pwm_freq_set",
    "IOConfigSubsystem.reverse_query",
    "IOConfigSubsystem.reverse_set",
    "IOConfigSubsystem.select",
    "IOConfigSubsystem.select_query",
    "IOConfigSubsystem.trigger_source_query",
    "IOConfigSubsystem.trigger_source_set",
    "IOConfigSubsystem.trigger_type_query",
    "IOConfigSubsystem.trigger_type_set",
    "InitiateSubsystem.acquire",
    "InitiateSubsystem.arb",
    "InitiateSubsystem.continuous_acq_query",
    "InitiateSubsystem.continuous_acq_set",
    "InitiateSubsystem.continuous_arb_query",
    "InitiateSubsystem.continuous_arb_set",
    "InitiateSubsystem.dlog",
    "InitiateSubsystem.elog",
    "LoggingSubsystem.DLOG.raw_data_query",
    "LoggingSubsystem.DLOG.state_query",
    "LoggingSubsystem.ELOG.raw_data_query",
    "LoggingSubsystem.ELOG.state_query",
    "MeasurementSubsystem.current_array_query",
    "MeasurementSubsystem.current_binary_array_query",
    "MeasurementSubsystem.current_high_query",
    "MeasurementSubsystem.current_low_query",
    "MeasurementSubsystem.current_max_query",
    "MeasurementSubsystem.current_min_query",
    "MeasurementSubsystem.current_query",
    "MeasurementSubsystem.power_array_query",
    "MeasurementSubsystem.power_binary_array_query",
    "MeasurementSubsystem.power_max_query",
    "MeasurementSubsystem.power_min_query",
    "MeasurementSubsystem.power_query",
    "MeasurementSubsystem.voltage_array_query",
    "MeasurementSubsystem.voltage_binary_array_query",
    "MeasurementSubsystem.voltage_high_query",
    "MeasurementSubsystem.voltage_low_query",
    "MeasurementSubsystem.voltage_max_query",
    "MeasurementSubsystem.voltage_min_query",
    "MeasurementSubsystem.voltage_query",
    "OutputSubsystem.delay_fall_query",
    "OutputSubsystem.delay_fall_set",
    "OutputSubsystem.delay_rise_query",
    "OutputSubsystem.delay_rise_set",
    "OutputSubsystem.inhibit_mode_query",
    "OutputSubsystem.inhibit_mode_set",
    "OutputSubsystem.power_on_mode_query",
    "OutputSubsystem.power_on_mode_set",
    "OutputSubsystem.protection_clear",
    "OutputSubsystem.state_query",
    "OutputSubsystem.state_set",
    "OutputSubsystem.watchdog_delay_query",
    "OutputSubsystem.watchdog_query",
    "OutputSubsystem.watchdog_set",
    "SenseSubsystem.acquisition_interval_query",
    "SenseSubsystem.acquisition_interval_set",
    "SenseSubsystem.acquisition_offset_query",
    "SenseSubsystem.acquisition_offset_set",
    "SenseSubsystem.acquisition_points_query",
    "SenseSubsystem.acquisition_points_set",
    "SourceSubsystem.cc_loop_speed_query",
    "SourceSubsystem.cc_loop_speed_set",
    "SourceSubsystem.current_both_time_query",
    "SourceSubsystem.current_both_time_set",
    "SourceSubsystem.current_fall_time_query",
    "SourceSubsystem.current_fall_time_set",
    "SourceSubsystem.current_limit_query",
    "SourceSubsystem.current_limit_set",
    "SourceSubsystem.current_query",
    "SourceSubsystem.current_rise_time_query",
    "SourceSubsystem.current_rise_time_set",
    "SourceSubsystem.current_set",
    "SourceSubsystem.cv_loop_speed_query",
    "SourceSubsystem.cv_loop_speed_set",
    "SourceSubsystem.external_coefficient_query",
    "SourceSubsystem.external_coefficient_set",
    "SourceSubsystem.external_programming_query",
    "SourceSubsystem.external_programming_set",
    "SourceSubsystem.function_mode_query",
    "SourceSubsystem.function_mode_set",
    "SourceSubsystem.function_query",
    "SourceSubsystem.function_set",
    "SourceSubsystem.ocp_delay_query",
    "SourceSubsystem.ocp_delay_set",
    "SourceSubsystem.ocp_enable",
    "SourceSubsystem.ocp_enable_query",
    "SourceSubsystem.ocp_query",
    "SourceSubsystem.ocp_set",
    "SourceSubsystem.opp_delay_query",
    "SourceSubsystem.opp_delay_set",
    "SourceSubsystem.opp_enable",
    "SourceSubsystem.opp_enable_query",
    "SourceSubsystem.opp_threshold_query",
    "SourceSubsystem.opp_threshold_set",
    "SourceSubsystem.output_power_limit_query",
    "SourceSubsystem.output_power_limit_set",
    "SourceSubsystem.ovp_delay_query",
    "SourceSubsystem.ovp_delay_set",
    "SourceSubsystem.ovp_enable",
    "SourceSubsystem.ovp_enable_query",
    "SourceSubsystem.ovp_query",
    "SourceSubsystem.ovp_set",
    "SourceSubsystem.power_limit_enable",
    "SourceSubsystem.power_limit_enable_query",
    "SourceSubsystem.power_limit_query",
    "SourceSubsystem.power_limit_set",
    "SourceSubsystem.programmed_power_limit_query",
    "SourceSubsystem.programmed_power_limit_set",
    "SourceSubsystem.remote_sense_query",
    "SourceSubsystem.remote_sense_set",
    "SourceSubsystem.resistance_query",
    "SourceSubsystem.resistance_set",
    "SourceSubsystem.transient_mode_query",
    "SourceSubsystem.transient_mode_set",
    "SourceSubsystem.ucp_delay_query",
    "SourceSubsystem.ucp_delay_set",
    "SourceSubsystem.ucp_enable",
    "SourceSubsystem.ucp_enable_query",
    "SourceSubsystem.ucp_query",
    "SourceSubsystem.ucp_set",
    "SourceSubsystem.ucp_warmup_query",
    "SourceSubsystem.ucp_warmup_set",
    "SourceSubsystem.uvp_delay_query",
    "SourceSubsystem.uvp_delay_set",
    "SourceSubsystem.uvp_enable",
    "SourceSubsystem.uvp_enable_query",
    "SourceSubsystem.uvp_query",
    "SourceSubsystem.uvp_set",
    "SourceSubsystem.uvp_warmup_query",
    "SourceSubsystem.uvp_warmup_set",
    "SourceSubsystem.voltage_both_time_query",
    "SourceSubsystem.voltage_both_time_set",
    "SourceSubsystem.voltage_fall_time_query",
    "SourceSubsystem.voltage_fall_time_set",
    "SourceSubsystem.voltage_limit_query",
    "SourceSubsystem.voltage_limit_set",
    "SourceSubsystem.voltage_query",
    "SourceSubsystem.voltage_rise_time_query",
    "SourceSubsystem.voltage_rise_time_set",
    "SourceSubsystem.voltage_set",
    "StatusSubsystem.oper_condition_query",
    "StatusSubsystem.oper_enable_query",
    "StatusSubsystem.oper_enable_set",
    "StatusSubsystem.oper_event_query",
    "StatusSubsystem.oper_negative_transition_query",
    "StatusSubsystem.oper_negative_transition_set",
    "StatusSubsystem.oper_positive_transition_query",
    "StatusSubsystem.oper_positive_transition_set",
    "StatusSubsystem.preset",
    "StatusSubsystem.ques_condition_query",
    "StatusSubsystem.ques_enable_query",
    "StatusSubsystem.ques_enable_set",
    "StatusSubsystem.ques_event_query",
    "StatusSubsystem.ques_negative_transition_query",
    "StatusSubsystem.ques_negative_transition_set",
    "StatusSubsystem.ques_positive_transition_query",
    "StatusSubsystem.ques_positive_transition_set",
    "StatusSubsystem.status_byte",
    "StatusSubsystem.std_event_enable_query",
    "StatusSubsystem.std_event_enable_set",
    "StatusSubsystem.std_event_register_query",
    "SystemSubsystem.beeper_immediate",
    "SystemSubsystem.beeper_state_query",
    "SystemSubsystem.beeper_state_set",
    "SystemSubsystem.clear",
    "SystemSubsystem.comm_gpib_addr_query",
    "SystemSubsystem.comm_gpib_addr_set",
    "SystemSubsystem.comm_select",
    "SystemSubsystem.comm_select_query",
    "SystemSubsystem.date_query",
    "SystemSubsystem.date_set",
    "SystemSubsystem.error",
    "SystemSubsystem.lan_gateway_query",
    "SystemSubsystem.lan_gateway_set",
    "SystemSubsystem.lan_ip_mode_query",
    "SystemSubsystem.lan_ip_mode_set",
    "SystemSubsystem.lan_ip_query",
    "SystemSubsystem.lan_ip_set",
    "SystemSubsystem.lan_subnet_query",
    "SystemSubsystem.lan_subnet_set",
    "SystemSubsystem.local",
    "SystemSubsystem.preset",
    "SystemSubsystem.remote",
    "SystemSubsystem.time_query",
    "SystemSubsystem.time_set",
    "SystemSubsystem.version",
    "TriggerSubsystem.acquire_arm",
    "TriggerSubsystem.acquire_current_level_query",
    "TriggerSubsystem.acquire_current_level_set",
    "TriggerSubsystem.acquire_immediate",
    "TriggerSubsystem.acquire_mode_query",
    "TriggerSubsystem.acquire_mode_set",
    "TriggerSubsystem.acquire_source_query",
    "TriggerSubsystem.acquire_source_set",
    "TriggerSubsystem.acquire_start",
    "TriggerSubsystem.acquire_voltage_level_query",
    "TriggerSubsystem.acquire_voltage_level_set",
    "TriggerSubsystem.arb_source_query",
    "TriggerSubsystem.arb_source_set",
    "TriggerSubsystem.delay_query",
    "TriggerSubsystem.delay_set",
    "TriggerSubsystem.dlog_source_query",
    "TriggerSubsystem.dlog_source_set",
    "TriggerSubsystem.elog_source_query",
    "TriggerSubsystem.elog_source_set",
    "TriggerSubsystem.elog_status_query",
    "TriggerSubsystem.elog_trigger_voltage_high_set",
    "TriggerSubsystem.elog_trigger_voltage_low_set",
    "TriggerSubsystem.hysteresis_query",
    "TriggerSubsystem.hysteresis_set",
    "TriggerSubsystem.hysteresis_threshold_query",
    "TriggerSubsystem.hysteresis_threshold_set",
    "TriggerSubsystem.level_query",
    "TriggerSubsystem.level_set",
    "TriggerSubsystem.source_query",
    "TriggerSubsystem.source_set",
))
RESTRICTED = frozenset((
    "AbortSubsystem.dlog", "AbortSubsystem.elog",
    "ArbSubsystem.terminate_last_set", "ArbSubsystem.terminate_last_query",
    "SourceSubsystem.remote_sense_query", "SystemSubsystem.preset",
    "BatterySubsystem.state_set", "BatterySubsystem.state_query",
    "SenseSubsystem.acquisition_points_query", "SenseSubsystem.acquisition_offset_query",
    "SenseSubsystem.acquisition_interval_query", "LoggingSubsystem.DLOG.raw_data_query",
    "TriggerSubsystem.source_set", "TriggerSubsystem.source_query",
    "TriggerSubsystem.level_set", "TriggerSubsystem.level_query",
    "TriggerSubsystem.delay_set", "TriggerSubsystem.delay_query",
    "TriggerSubsystem.hysteresis_set", "TriggerSubsystem.hysteresis_query",
))


@dataclass(frozen=True)
class MethodEvidence:
    state: CapabilityState
    reference: str

    def __post_init__(self):
        if not isinstance(self.state, CapabilityState):
            raise ConfigurationError("explicit CapabilityState required")
        if not isinstance(self.reference, str) or not self.reference.strip():
            raise ConfigurationError("evidence reference required")


@dataclass(frozen=True)
class MethodQualification:
    model: str
    firmware: str
    interface: str
    methods: Mapping[str, MethodEvidence]

    def __post_init__(self):
        if not isinstance(self.model, str) or self.model not in MODEL_DESCRIPTORS:
            raise ConfigurationError("exact rated model required")
        if not isinstance(self.firmware, str) or not self.firmware.strip() or self.firmware.strip().upper() in ("UNKNOWN", "N/A", "NONE"):
            raise ConfigurationError("exact firmware required")
        if not isinstance(self.interface, str) or not self.interface.strip():
            raise ConfigurationError("exact core transport descriptor kind required")
        if not isinstance(self.methods, Mapping):
            raise ConfigurationError("method evidence map required")
        copy = dict(self.methods)
        for key, evidence in copy.items():
            if key not in METHOD_KEYS or not isinstance(evidence, MethodEvidence):
                raise ConfigurationError(f"unknown method or invalid evidence: {key}")
            if key in RESTRICTED and evidence.state is CapabilityState.SUPPORTED:
                raise ConfigurationError(f"quarantined operation cannot be enabled: {key}")
        object.__setattr__(self, "methods", MappingProxyType(copy))

    def state(self, key):
        if key in RESTRICTED:
            return CapabilityState.UNQUALIFIED
        evidence = self.methods.get(key)
        return evidence.state if evidence is not None else CapabilityState.UNKNOWN

    def require(self, key):
        state = self.state(key)
        if state is not CapabilityState.SUPPORTED:
            raise UnsupportedOperationError(f"{key} is {state.value} for {self.model}/{self.firmware}/{self.interface}")


def install_subsystem_guards(classes):
    """Install guards on the actual subsystem classes, including direct instances.

    No per-instance closure or reflection-based replacement is needed during
    instrument construction. This preserves signatures and isinstance checks.
    """
    def guard(method, prefix):
        @wraps(method)
        def wrapped(self, *args, **kwargs):
            key = prefix
            if prefix.startswith("LoggingSubsystem."):
                key = "LoggingSubsystem." + self._kind + "." + method.__name__
            scope = getattr(self._p, "_qualified_method_scope", None)
            if scope is None:
                # Compatibility for non-ITECH parents and standalone mocks.
                return method(self, *args, **kwargs)
            with scope(key):
                return method(self, *args, **kwargs)
        return wrapped
    found = set()
    for cls in classes:
        prefix = cls.__name__
        for name, method in inspect.getmembers(cls, inspect.isfunction):
            if name.startswith("_") or (prefix == "IEEE488" and name == "idn"):
                continue
            key = prefix + "." + name
            keys = ({"LoggingSubsystem.ELOG." + name, "LoggingSubsystem.DLOG." + name}
                    if prefix == "LoggingSubsystem" else {key})
            if not keys <= METHOD_KEYS:
                raise ConfigurationError(f"missing subsystem qualification key {key}")
            setattr(cls, name, guard(method, key))
            found.update(keys)
    if found != METHOD_KEYS:
        raise ConfigurationError("subsystem qualification inventory mismatch")
