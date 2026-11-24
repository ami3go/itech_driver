"""Typed command specifications for migrated runtime operations.

The inventory in docs/command_registry.json remains historical coverage.
A runtime spec establishes software wire syntax, not hardware qualification.
"""
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

from scpi_driver_core import ConfigurationError, UnsupportedOperationError
from scpi_driver_core.scpi.parsers import parse_bool, parse_float, parse_int
from .utils.validation import strict_bool


class ResultKind(str, Enum):
    FLOAT = "float"
    BOOL = "bool"
    ASCII_ARRAY = "ascii_array"
    BINARY_ARRAY = "binary_array"
    BOOL_WRITE = "bool_write"
    RAW = "raw"
    INT = "int"
    VOID_WRITE = "void_write"
    PARAM_WRITE = "param_write"
    PARAM_QUERY = "param_query"
    HELPER = "helper"


@dataclass(frozen=True)
class CommandSpec:
    method: str
    header: str
    kind: ResultKind
    feature: str
    guide_status: str = "unverified"
    guide_page: int | None = None
    replay: str = "never"
    effect: str = "unknown_read"
    parameters: tuple[str, ...] = ()

    @property
    def modifies_state(self) -> bool:
        return self.kind in (ResultKind.BOOL_WRITE, ResultKind.VOID_WRITE, ResultKind.PARAM_WRITE) or self.effect in ("write", "destructive_read")


_ROWS = (
    ("MeasurementSubsystem.voltage_query", "MEAS:VOLT?", ResultKind.FLOAT, "measurement"),
    ("MeasurementSubsystem.voltage_high_query", "MEAS:VOLT:HIGH?", ResultKind.FLOAT, "measurement"),
    ("MeasurementSubsystem.voltage_low_query", "MEAS:VOLT:LOW?", ResultKind.FLOAT, "measurement"),
    ("MeasurementSubsystem.voltage_max_query", "MEAS:VOLT:MAX?", ResultKind.FLOAT, "measurement"),
    ("MeasurementSubsystem.voltage_min_query", "MEAS:VOLT:MIN?", ResultKind.FLOAT, "measurement"),
    ("MeasurementSubsystem.current_query", "MEAS:CURR?", ResultKind.FLOAT, "measurement"),
    ("MeasurementSubsystem.current_high_query", "MEAS:CURR:HIGH?", ResultKind.FLOAT, "measurement"),
    ("MeasurementSubsystem.current_low_query", "MEAS:CURR:LOW?", ResultKind.FLOAT, "measurement"),
    ("MeasurementSubsystem.current_max_query", "MEAS:CURR:MAX?", ResultKind.FLOAT, "measurement"),
    ("MeasurementSubsystem.current_min_query", "MEAS:CURR:MIN?", ResultKind.FLOAT, "measurement"),
    ("MeasurementSubsystem.power_query", "MEAS:POW?", ResultKind.FLOAT, "measurement"),
    ("MeasurementSubsystem.power_max_query", "MEAS:POW:MAX?", ResultKind.FLOAT, "measurement"),
    ("MeasurementSubsystem.power_min_query", "MEAS:POW:MIN?", ResultKind.FLOAT, "measurement"),
    ("MeasurementSubsystem.current_binary_array_query", "MEAS:ARR:CURR?", ResultKind.BINARY_ARRAY, "measurement"),
    ("MeasurementSubsystem.power_binary_array_query", "MEAS:ARR:POW?", ResultKind.BINARY_ARRAY, "measurement"),
    ("MeasurementSubsystem.voltage_array_query", "MEAS:ARR:VOLT?", ResultKind.ASCII_ARRAY, "measurement"),
    ("MeasurementSubsystem.current_array_query", "MEAS:ARR:CURR?", ResultKind.ASCII_ARRAY, "measurement"),
    ("MeasurementSubsystem.power_array_query", "MEAS:ARR:POW?", ResultKind.ASCII_ARRAY, "measurement"),
    ("FetchSubsystem.voltage_query", "FETC:VOLT?", ResultKind.FLOAT, "fetch"),
    ("FetchSubsystem.voltage_high_query", "FETC:VOLT:HIGH?", ResultKind.FLOAT, "fetch"),
    ("FetchSubsystem.voltage_low_query", "FETC:VOLT:LOW?", ResultKind.FLOAT, "fetch"),
    ("FetchSubsystem.voltage_max_query", "FETC:VOLT:MAX?", ResultKind.FLOAT, "fetch"),
    ("FetchSubsystem.voltage_min_query", "FETC:VOLT:MIN?", ResultKind.FLOAT, "fetch"),
    ("FetchSubsystem.current_query", "FETC:CURR?", ResultKind.FLOAT, "fetch"),
    ("FetchSubsystem.current_high_query", "FETC:CURR:HIGH?", ResultKind.FLOAT, "fetch"),
    ("FetchSubsystem.current_low_query", "FETC:CURR:LOW?", ResultKind.FLOAT, "fetch"),
    ("FetchSubsystem.current_max_query", "FETC:CURR:MAX?", ResultKind.FLOAT, "fetch"),
    ("FetchSubsystem.current_min_query", "FETC:CURR:MIN?", ResultKind.FLOAT, "fetch"),
    ("FetchSubsystem.power_query", "FETC:POW?", ResultKind.FLOAT, "fetch"),
    ("FetchSubsystem.power_max_query", "FETC:POW:MAX?", ResultKind.FLOAT, "fetch"),
    ("FetchSubsystem.power_min_query", "FETC:POW:MIN?", ResultKind.FLOAT, "fetch"),
    ("FetchSubsystem.current_binary_array_query", "FETC:ARR:CURR?", ResultKind.BINARY_ARRAY, "fetch"),
    ("FetchSubsystem.power_binary_array_query", "FETC:ARR:POW?", ResultKind.BINARY_ARRAY, "fetch"),
    ("FetchSubsystem.voltage_array_query", "FETC:ARR:VOLT?", ResultKind.ASCII_ARRAY, "fetch"),
    ("FetchSubsystem.current_array_query", "FETC:ARR:CURR?", ResultKind.ASCII_ARRAY, "fetch"),
    ("FetchSubsystem.power_array_query", "FETC:ARR:POW?", ResultKind.ASCII_ARRAY, "fetch"),
    ("MeasurementSubsystem.voltage_binary_array_query", "MEAS:ARR:VOLT?", ResultKind.BINARY_ARRAY, "measurement"),
    ("FetchSubsystem.voltage_binary_array_query", "FETC:ARR:VOLT?", ResultKind.BINARY_ARRAY, "fetch"),
    ("OutputSubsystem.state_set", "OUTP:STAT", ResultKind.BOOL_WRITE, "output_control"),
    ("OutputSubsystem.state_query", "OUTP:STAT?", ResultKind.BOOL, "output_control"),
)
_ADDITIONAL_ROWS = (
    ("SourceSubsystem.voltage_query", "SOUR:VOLT?", ResultKind.FLOAT, "SourceSubsystem", "read"),
    ("SourceSubsystem.current_query", "SOUR:CURR?", ResultKind.FLOAT, "SourceSubsystem", "read"),
    ("SourceSubsystem.opp_enable_query", "SOUR:POW:OVER:PROT:STAT?", ResultKind.BOOL, "SourceSubsystem", "read"),
    ("SourceSubsystem.uvp_enable_query", "SOUR:VOLT:UND:PROT:STAT?", ResultKind.BOOL, "SourceSubsystem", "read"),
    ("SourceSubsystem.ucp_enable_query", "SOUR:CURR:UND:PROT:STAT?", ResultKind.BOOL, "SourceSubsystem", "read"),
    ("SourceSubsystem.external_programming_query", "SOUR:EXT:PROG?", ResultKind.BOOL, "SourceSubsystem", "read"),
    ("OutputSubsystem.delay_rise_query", "OUTP:DELay:RISE?", ResultKind.FLOAT, "OutputSubsystem", "read"),
    ("OutputSubsystem.delay_fall_query", "OUTP:DELay:FALL?", ResultKind.FLOAT, "OutputSubsystem", "read"),
    ("OutputSubsystem.inhibit_mode_query", "OUTP:INHibit:MODE?", ResultKind.RAW, "OutputSubsystem", "read"),
    ("OutputSubsystem.protection_clear", "OUTP:PROTection:CLEar", ResultKind.VOID_WRITE, "OutputSubsystem", "write"),
    ("OutputSubsystem.watchdog_query", "OUTP:PROT:WDOG:STAT?", ResultKind.BOOL, "OutputSubsystem", "read"),
    ("SystemSubsystem.version", "SYST:VERSion?", ResultKind.RAW, "SystemSubsystem", "read"),
    ("SystemSubsystem.error", "SYST:ERRor?", ResultKind.RAW, "SystemSubsystem", "destructive_read"),
    ("SystemSubsystem.clear", "SYST:CLEar", ResultKind.VOID_WRITE, "SystemSubsystem", "write"),
    ("SystemSubsystem.remote", "SYST:REMote", ResultKind.VOID_WRITE, "SystemSubsystem", "write"),
    ("SystemSubsystem.local", "SYST:LOCal", ResultKind.VOID_WRITE, "SystemSubsystem", "write"),
    ("SystemSubsystem.beeper_immediate", "SYST:BEEPer:IMMediate", ResultKind.VOID_WRITE, "SystemSubsystem", "write"),
    ("SystemSubsystem.beeper_state_query", "SYST:BEEPer:STATe?", ResultKind.BOOL, "SystemSubsystem", "read"),
    ("SystemSubsystem.date_query", "SYST:DATE?", ResultKind.RAW, "SystemSubsystem", "read"),
    ("SystemSubsystem.time_query", "SYST:TIME?", ResultKind.RAW, "SystemSubsystem", "read"),
    ("SystemSubsystem.comm_select_query", "SYST:COMMunicate:SELect?", ResultKind.RAW, "SystemSubsystem", "read"),
    ("SystemSubsystem.comm_gpib_addr_query", "SYST:COMMunicate:GPIB:ADDRess?", ResultKind.INT, "SystemSubsystem", "read"),
    ("StatusSubsystem.preset", "STAT:PRES", ResultKind.VOID_WRITE, "StatusSubsystem", "write"),
    ("StatusSubsystem.oper_condition_query", "STAT:OPER:COND?", ResultKind.INT, "StatusSubsystem", "read"),
    ("StatusSubsystem.oper_event_query", "STAT:OPER:EVEN?", ResultKind.INT, "StatusSubsystem", "destructive_read"),
    ("StatusSubsystem.ques_condition_query", "STAT:QUES:COND?", ResultKind.INT, "StatusSubsystem", "read"),
    ("StatusSubsystem.ques_event_query", "STAT:QUES:EVEN?", ResultKind.INT, "StatusSubsystem", "destructive_read"),
    ("TriggerSubsystem.acquire_immediate", "TRIG:ACQuire:IMMediate", ResultKind.VOID_WRITE, "TriggerSubsystem", "write"),
    ("TriggerSubsystem.acquire_arm", "INIT:ACQ", ResultKind.VOID_WRITE, "TriggerSubsystem", "write"),
    ("TriggerSubsystem.acquire_mode_query", "TRIG:ACQ:MODE?", ResultKind.RAW, "TriggerSubsystem", "read"),
    ("TriggerSubsystem.acquire_voltage_level_query", "TRIG:ACQ:VOLT:LEV?", ResultKind.FLOAT, "TriggerSubsystem", "read"),
    ("TriggerSubsystem.acquire_current_level_query", "TRIG:ACQ:CURR:LEV?", ResultKind.FLOAT, "TriggerSubsystem", "read"),
    ("TriggerSubsystem.elog_status_query", "ELOG:STAT?", ResultKind.RAW, "TriggerSubsystem", "read"),
    ("BatterySubsystem.charge_voltage_query", "BATT:CHAR:VOLT?", ResultKind.FLOAT, "BatterySubsystem", "read"),
    ("BatterySubsystem.charge_current_query", "BATT:CHAR:CURR?", ResultKind.FLOAT, "BatterySubsystem", "read"),
    ("BatterySubsystem.shutdown_voltage_query", "BATT:SHUT:VOLT?", ResultKind.FLOAT, "BatterySubsystem", "read"),
    ("BatterySubsystem.shutdown_current_query", "BATT:SHUT:CURR?", ResultKind.FLOAT, "BatterySubsystem", "read"),
    ("BatterySubsystem.shutdown_capacity_query", "BATT:SHUT:CAP?", ResultKind.FLOAT, "BatterySubsystem", "read"),
    ("BatterySubsystem.shutdown_time_query", "BATT:SHUT:TIME?", ResultKind.FLOAT, "BatterySubsystem", "read"),
    ("BatterySubsystem.mode_set", "SOUR:FUNC:MODE BATT", ResultKind.VOID_WRITE, "BatterySubsystem", "write"),
    ("InitiateSubsystem.acquire", "INITiate:ACQuire", ResultKind.VOID_WRITE, "InitiateSubsystem", "write"),
    ("InitiateSubsystem.arb", "INITiate:ARB", ResultKind.VOID_WRITE, "InitiateSubsystem", "write"),
    ("InitiateSubsystem.continuous_arb_query", "INITiate:CONTinuous:ARB?", ResultKind.BOOL, "InitiateSubsystem", "read"),
    ("InitiateSubsystem.continuous_acq_query", "INITiate:CONTinuous:ACQuire?", ResultKind.BOOL, "InitiateSubsystem", "read"),
    ("InitiateSubsystem.dlog", "INITiate:DLOG", ResultKind.VOID_WRITE, "InitiateSubsystem", "write"),
    ("InitiateSubsystem.elog", "INITiate:ELOG", ResultKind.VOID_WRITE, "InitiateSubsystem", "write"),
    ("AbortSubsystem.acquire", "ABORt:ACQuire", ResultKind.VOID_WRITE, "AbortSubsystem", "write"),
    ("AbortSubsystem.arb", "ABORt:ARB", ResultKind.VOID_WRITE, "AbortSubsystem", "write"),
)
_PARAMETERIZED_ROWS = (
    ("ArbSubsystem.function_shape_set", "ARB:FUNCTION:SHAPE", ResultKind.PARAM_WRITE, "ArbSubsystem", "write", ("validated_payload",)),
    ("ArbSubsystem.function_shape_query", "ARB:FUNCTION:SHAPE?", ResultKind.RAW, "ArbSubsystem", "unknown_read", ()),
    ("ArbSubsystem.function_type_set", "ARB:FUNCTION:TYPE", ResultKind.PARAM_WRITE, "ArbSubsystem", "write", ("validated_payload",)),
    ("ArbSubsystem.function_type_query", "ARB:FUNCTION:TYPE?", ResultKind.RAW, "ArbSubsystem", "unknown_read", ()),
    ("ArbSubsystem.udef_count_set", "ARB:UDEFined:COUNt", ResultKind.PARAM_WRITE, "ArbSubsystem", "write", ("validated_payload",)),
    ("ArbSubsystem.udef_count_query", "ARB:UDEFined:COUNt?", ResultKind.RAW, "ArbSubsystem", "unknown_read", ()),
    ("ArbSubsystem.udef_level_set", "ARB:UDEFined:LEVel", ResultKind.PARAM_WRITE, "ArbSubsystem", "write", ("validated_payload",)),
    ("ArbSubsystem.udef_level_query", "ARB:UDEFined:LEVel?", ResultKind.PARAM_QUERY, "ArbSubsystem", "unknown_read", ("validated_payload",)),
    ("ArbSubsystem.udef_dwell_set", "ARB:UDEFined:DWELl", ResultKind.PARAM_WRITE, "ArbSubsystem", "write", ("validated_payload",)),
    ("ArbSubsystem.udef_dwell_query", "ARB:UDEFined:DWELl?", ResultKind.PARAM_QUERY, "ArbSubsystem", "unknown_read", ("validated_payload",)),
    ("ArbSubsystem.udef_slew_set", "ARB:UDEFined:SLEW", ResultKind.PARAM_WRITE, "ArbSubsystem", "write", ("validated_payload",)),
    ("ArbSubsystem.udef_slew_query", "ARB:UDEFined:SLEW?", ResultKind.PARAM_QUERY, "ArbSubsystem", "unknown_read", ("validated_payload",)),
    ("ArbSubsystem.count_set", "ARB:COUNT", ResultKind.PARAM_WRITE, "ArbSubsystem", "write", ("validated_payload",)),
    ("ArbSubsystem.count_query", "ARB:COUNT?", ResultKind.RAW, "ArbSubsystem", "unknown_read", ()),
    ("ArbSubsystem.save", "ARB:SAVE", ResultKind.PARAM_WRITE, "ArbSubsystem", "write", ("validated_payload",)),
    ("ArbSubsystem.recall", "ARB:RECall", ResultKind.PARAM_WRITE, "ArbSubsystem", "write", ("validated_payload",)),
    ("ArbSubsystem.pause_set", "ARB:PAUSe:STATe", ResultKind.PARAM_WRITE, "ArbSubsystem", "write", ("validated_payload",)),
    ("ArbSubsystem.pause_query", "ARB:PAUSe:STATe?", ResultKind.RAW, "ArbSubsystem", "unknown_read", ()),
    ("ArbSubsystem.state_query", "ARB:EXE:STAT?", ResultKind.RAW, "ArbSubsystem", "unknown_read", ()),
    ("SourceSubsystem.function_set", "SOUR:FUNC", ResultKind.PARAM_WRITE, "SourceSubsystem", "write", ("validated_payload",)),
    ("SourceSubsystem.function_query", "SOUR:FUNC", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.function_mode_set", "SOUR:FUNC:MODE", ResultKind.PARAM_WRITE, "SourceSubsystem", "write", ("validated_payload",)),
    ("SourceSubsystem.function_mode_query", "SOUR:FUNC:MODE", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.voltage_set", "SOUR:VOLT", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("SourceSubsystem.current_set", "SOUR:CURR", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("SourceSubsystem.ovp_enable", "SOUR:VOLT:OVER:PROT:STAT", ResultKind.PARAM_WRITE, "SourceSubsystem", "write", ("validated_payload",)),
    ("SourceSubsystem.ocp_enable", "SOUR:CURR:OVER:PROT:STAT", ResultKind.PARAM_WRITE, "SourceSubsystem", "write", ("validated_payload",)),
    ("SourceSubsystem.opp_enable", "SOUR:POW:OVER:PROT:STAT", ResultKind.PARAM_WRITE, "SourceSubsystem", "write", ("validated_payload",)),
    ("SourceSubsystem.output_power_limit_set", "SOUR:POW:LIM", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("SourceSubsystem.output_power_limit_query", "SOUR:POW:LIM", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.voltage_limit_set", "SOUR:VOLT:LIM", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("SourceSubsystem.voltage_limit_query", "SOUR:VOLT:LIM", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.current_limit_set", "SOUR:CURR:LIM", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("SourceSubsystem.current_limit_query", "SOUR:CURR:LIM", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.programmed_power_limit_set", "SOUR:POW:LIM", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("SourceSubsystem.programmed_power_limit_query", "SOUR:POW:LIM", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.remote_sense_set", "SOUR:REM:SENS:STAT", ResultKind.PARAM_WRITE, "SourceSubsystem", "write", ("validated_payload",)),
    ("SourceSubsystem.ovp_delay_set", "SOUR:VOLT:OVER:PROT:DEL", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("SourceSubsystem.ovp_delay_query", "SOUR:VOLT:OVER:PROT:DEL", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.ocp_delay_set", "SOUR:CURR:OVER:PROT:DEL", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("SourceSubsystem.ocp_delay_query", "SOUR:CURR:OVER:PROT:DEL", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.opp_delay_set", "SOUR:POW:OVER:PROT:DEL", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("SourceSubsystem.opp_delay_query", "SOUR:POW:OVER:PROT:DEL", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.uvp_delay_set", "SOUR:VOLT:UND:PROT:DEL", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("SourceSubsystem.uvp_delay_query", "SOUR:VOLT:UND:PROT:DEL", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.ucp_delay_set", "SOUR:CURR:UND:PROT:DEL", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("SourceSubsystem.ucp_delay_query", "SOUR:CURR:UND:PROT:DEL", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.uvp_warmup_set", "SOUR:VOLT:UND:PROT:WARM", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("SourceSubsystem.uvp_warmup_query", "SOUR:VOLT:UND:PROT:WARM", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.ucp_warmup_set", "SOUR:CURR:UND:PROT:WARM", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("SourceSubsystem.ucp_warmup_query", "SOUR:CURR:UND:PROT:WARM", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.uvp_enable", "SOUR:VOLT:UND:PROT:STAT", ResultKind.PARAM_WRITE, "SourceSubsystem", "write", ("validated_payload",)),
    ("SourceSubsystem.ucp_enable", "SOUR:CURR:UND:PROT:STAT", ResultKind.PARAM_WRITE, "SourceSubsystem", "write", ("validated_payload",)),
    ("SourceSubsystem.voltage_rise_time_set", "SOUR:VOLT:SLEW:POS", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("SourceSubsystem.voltage_rise_time_query", "SOUR:VOLT:SLEW:POS", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.voltage_fall_time_set", "SOUR:VOLT:SLEW:NEG", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("SourceSubsystem.voltage_fall_time_query", "SOUR:VOLT:SLEW:NEG", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.voltage_both_time_set", "SOUR:VOLT:SLEW:BOTH", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("SourceSubsystem.voltage_both_time_query", "SOUR:VOLT:SLEW:BOTH", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.current_rise_time_set", "SOUR:CURR:SLEW:POS", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("SourceSubsystem.current_rise_time_query", "SOUR:CURR:SLEW:POS", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.current_fall_time_set", "SOUR:CURR:SLEW:NEG", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("SourceSubsystem.current_fall_time_query", "SOUR:CURR:SLEW:NEG", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.current_both_time_set", "SOUR:CURR:SLEW:BOTH", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("SourceSubsystem.current_both_time_query", "SOUR:CURR:SLEW:BOTH", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.cv_loop_speed_set", "SOUR:CV:PRI", ResultKind.PARAM_WRITE, "SourceSubsystem", "write", ("validated_payload",)),
    ("SourceSubsystem.cv_loop_speed_query", "SOUR:CV:PRI", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.cc_loop_speed_set", "SOUR:CC:PRI", ResultKind.PARAM_WRITE, "SourceSubsystem", "write", ("validated_payload",)),
    ("SourceSubsystem.cc_loop_speed_query", "SOUR:CC:PRI", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.resistance_query", "SOUR:RES", ResultKind.HELPER, "SourceSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SourceSubsystem.resistance_set", "SOUR:RES", ResultKind.HELPER, "SourceSubsystem", "write", ("validated_by_subsystem",)),
    ("StatusSubsystem.oper_enable_set", "STAT:OPER:ENAB", ResultKind.HELPER, "StatusSubsystem", "write", ("validated_by_subsystem",)),
    ("StatusSubsystem.oper_enable_query", "STAT:OPER:ENAB", ResultKind.HELPER, "StatusSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("StatusSubsystem.ques_enable_set", "STAT:QUES:ENAB", ResultKind.HELPER, "StatusSubsystem", "write", ("validated_by_subsystem",)),
    ("StatusSubsystem.ques_enable_query", "STAT:QUES:ENAB", ResultKind.HELPER, "StatusSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("StatusSubsystem.oper_positive_transition_set", "STAT:OPER:PTR", ResultKind.HELPER, "StatusSubsystem", "write", ("validated_by_subsystem",)),
    ("StatusSubsystem.oper_positive_transition_query", "STAT:OPER:PTR", ResultKind.HELPER, "StatusSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("StatusSubsystem.oper_negative_transition_set", "STAT:OPER:NTR", ResultKind.HELPER, "StatusSubsystem", "write", ("validated_by_subsystem",)),
    ("StatusSubsystem.oper_negative_transition_query", "STAT:OPER:NTR", ResultKind.HELPER, "StatusSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("StatusSubsystem.ques_positive_transition_set", "STAT:QUES:PTR", ResultKind.HELPER, "StatusSubsystem", "write", ("validated_by_subsystem",)),
    ("StatusSubsystem.ques_positive_transition_query", "STAT:QUES:PTR", ResultKind.HELPER, "StatusSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("StatusSubsystem.ques_negative_transition_set", "STAT:QUES:NTR", ResultKind.HELPER, "StatusSubsystem", "write", ("validated_by_subsystem",)),
    ("StatusSubsystem.ques_negative_transition_query", "STAT:QUES:NTR", ResultKind.HELPER, "StatusSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("IOConfigSubsystem.select", "IO:SELect", ResultKind.PARAM_WRITE, "IOConfigSubsystem", "write", ("validated_payload",)),
    ("IOConfigSubsystem.select_query", "IO:SELect?", ResultKind.RAW, "IOConfigSubsystem", "unknown_read", ()),
    ("IOConfigSubsystem.direction_set", "IO:DIRE", ResultKind.PARAM_WRITE, "IOConfigSubsystem", "write", ("validated_payload",)),
    ("IOConfigSubsystem.direction_query", "IO:DIRE?", ResultKind.PARAM_QUERY, "IOConfigSubsystem", "unknown_read", ("validated_payload",)),
    ("IOConfigSubsystem.pwm_enable", "IO:PWM:ENABle", ResultKind.PARAM_WRITE, "IOConfigSubsystem", "write", ("validated_payload",)),
    ("IOConfigSubsystem.pwm_freq_set", "IO:PWM:FREQuency", ResultKind.PARAM_WRITE, "IOConfigSubsystem", "write", ("validated_payload",)),
    ("IOConfigSubsystem.pwm_duty_set", "IO:PWM:DUTY", ResultKind.PARAM_WRITE, "IOConfigSubsystem", "write", ("validated_payload",)),
    ("IOConfigSubsystem.reverse_set", "IO:REVE", ResultKind.PARAM_WRITE, "IOConfigSubsystem", "write", ("validated_payload",)),
    ("IOConfigSubsystem.reverse_query", "IO:REVE?", ResultKind.PARAM_QUERY, "IOConfigSubsystem", "unknown_read", ("validated_payload",)),
    ("IOConfigSubsystem.pwm_enable_query", "IO:PWM?", ResultKind.PARAM_QUERY, "IOConfigSubsystem", "unknown_read", ("validated_payload",)),
    ("IOConfigSubsystem.pwm_freq_query", "IO:PWM:FREQ", ResultKind.HELPER, "IOConfigSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("IOConfigSubsystem.pwm_duty_query", "IO:PWM:DUTY?", ResultKind.PARAM_QUERY, "IOConfigSubsystem", "unknown_read", ("validated_payload",)),
    ("IOConfigSubsystem.pulse_width_query", "IO:PULS:WIDT", ResultKind.HELPER, "IOConfigSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("IOConfigSubsystem.pulse_width_set", "IO:PULS:WIDT", ResultKind.PARAM_WRITE, "IOConfigSubsystem", "write", ("validated_payload",)),
    ("IOConfigSubsystem.pin_function_set", "IO:TYPE", ResultKind.PARAM_WRITE, "IOConfigSubsystem", "write", ("validated_payload",)),
    ("IOConfigSubsystem.pin_function_query", "IO:TYPE?", ResultKind.PARAM_QUERY, "IOConfigSubsystem", "unknown_read", ("validated_payload",)),
    ("IOConfigSubsystem.trigger_type_set", "IO:TRIG:TYPE", ResultKind.HELPER, "IOConfigSubsystem", "write", ("validated_by_subsystem",)),
    ("IOConfigSubsystem.trigger_type_query", "IO:TRIG:TYPE", ResultKind.HELPER, "IOConfigSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("IOConfigSubsystem.trigger_source_set", "IO:TRIG:SOUR", ResultKind.HELPER, "IOConfigSubsystem", "write", ("validated_by_subsystem",)),
    ("IOConfigSubsystem.trigger_source_query", "IO:TRIG:SOUR", ResultKind.HELPER, "IOConfigSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("IOConfigSubsystem.output_level_set", "IO:OUTP:LEV", ResultKind.PARAM_WRITE, "IOConfigSubsystem", "write", ("validated_payload",)),
    ("IOConfigSubsystem.output_level_query", "IO:OUTP:LEV", ResultKind.HELPER, "IOConfigSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("IOConfigSubsystem.input_level_query", "IO:INP:LEV", ResultKind.HELPER, "IOConfigSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SenseSubsystem.acquisition_points_set", "SENS:ACQ:POIN", ResultKind.PARAM_WRITE, "SenseSubsystem", "write", ("validated_payload",)),
    ("SenseSubsystem.acquisition_offset_set", "SENS:ACQ:OFFS:POIN", ResultKind.PARAM_WRITE, "SenseSubsystem", "write", ("validated_payload",)),
    ("SenseSubsystem.acquisition_interval_set", "SENS:ACQ:TINT", ResultKind.PARAM_WRITE, "SenseSubsystem", "write", ("validated_payload",)),
    ("BatterySubsystem.charge_voltage_set", "BATT:CHAR:VOLT", ResultKind.PARAM_WRITE, "BatterySubsystem", "write", ("validated_payload",)),
    ("BatterySubsystem.charge_current_set", "BATT:CHAR:CURR", ResultKind.PARAM_WRITE, "BatterySubsystem", "write", ("validated_payload",)),
    ("BatterySubsystem.shutdown_voltage_set", "BATT:SHUT:VOLT", ResultKind.PARAM_WRITE, "BatterySubsystem", "write", ("validated_payload",)),
    ("BatterySubsystem.shutdown_current_set", "BATT:SHUT:CURR", ResultKind.PARAM_WRITE, "BatterySubsystem", "write", ("validated_payload",)),
    ("BatterySubsystem.shutdown_capacity_set", "BATT:SHUT:CAP", ResultKind.PARAM_WRITE, "BatterySubsystem", "write", ("validated_payload",)),
    ("BatterySubsystem.shutdown_time_set", "BATT:SHUT:TIME", ResultKind.PARAM_WRITE, "BatterySubsystem", "write", ("validated_payload",)),
    ("BatterySubsystem.mode_query", "SOUR:FUNC:MODE?", ResultKind.RAW, "BatterySubsystem", "unknown_read", ()),
    ("OutputSubsystem.delay_rise_set", "OUTP:DELay:RISE", ResultKind.PARAM_WRITE, "OutputSubsystem", "write", ("validated_payload",)),
    ("OutputSubsystem.delay_fall_set", "OUTP:DELay:FALL", ResultKind.PARAM_WRITE, "OutputSubsystem", "write", ("validated_payload",)),
    ("OutputSubsystem.inhibit_mode_set", "OUTP:INHibit:MODE", ResultKind.PARAM_WRITE, "OutputSubsystem", "write", ("validated_payload",)),
    ("OutputSubsystem.watchdog_delay_query", "OUTP:PROT:WDOG:DEL?", ResultKind.RAW, "OutputSubsystem", "unknown_read", ()),
    ("OutputSubsystem.power_on_mode_set", "OUTP:PON:STAT", ResultKind.PARAM_WRITE, "OutputSubsystem", "write", ("validated_payload",)),
    ("OutputSubsystem.power_on_mode_query", "OUTP:PON:STAT?", ResultKind.RAW, "OutputSubsystem", "unknown_read", ()),
    ("SystemSubsystem.beeper_state_set", "SYST:BEEPer:STATe", ResultKind.PARAM_WRITE, "SystemSubsystem", "write", ("validated_payload",)),
    ("SystemSubsystem.date_set", "SYST:DATE", ResultKind.PARAM_WRITE, "SystemSubsystem", "write", ("validated_payload",)),
    ("SystemSubsystem.time_set", "SYST:TIME", ResultKind.PARAM_WRITE, "SystemSubsystem", "write", ("validated_payload",)),
    ("SystemSubsystem.comm_select", "SYST:COMMunicate:SELect", ResultKind.PARAM_WRITE, "SystemSubsystem", "write", ("validated_payload",)),
    ("SystemSubsystem.comm_gpib_addr_set", "SYST:COMMunicate:GPIB:ADDRess", ResultKind.PARAM_WRITE, "SystemSubsystem", "write", ("validated_payload",)),
    ("SystemSubsystem.lan_ip_set", "SYST:COMM:LAN:IP", ResultKind.HELPER, "SystemSubsystem", "write", ("validated_by_subsystem",)),
    ("SystemSubsystem.lan_ip_query", "SYST:COMM:LAN:IP", ResultKind.HELPER, "SystemSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SystemSubsystem.lan_subnet_set", "SYST:COMM:LAN:SMAS", ResultKind.HELPER, "SystemSubsystem", "write", ("validated_by_subsystem",)),
    ("SystemSubsystem.lan_subnet_query", "SYST:COMM:LAN:SMAS", ResultKind.HELPER, "SystemSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SystemSubsystem.lan_gateway_set", "SYST:COMM:LAN:DGAT", ResultKind.HELPER, "SystemSubsystem", "write", ("validated_by_subsystem",)),
    ("SystemSubsystem.lan_gateway_query", "SYST:COMM:LAN:DGAT", ResultKind.HELPER, "SystemSubsystem", "unknown_read", ("validated_by_subsystem",)),
    ("SystemSubsystem.lan_ip_mode_set", "SYST:COMM:LAN:IP:MODE", ResultKind.PARAM_WRITE, "SystemSubsystem", "write", ("validated_payload",)),
    ("SystemSubsystem.lan_ip_mode_query", "SYST:COMM:LAN:IP:MODE?", ResultKind.RAW, "SystemSubsystem", "unknown_read", ()),
    ("TriggerSubsystem.acquire_mode_set", "TRIG:ACQ:MODE", ResultKind.PARAM_WRITE, "TriggerSubsystem", "write", ("validated_payload",)),
    ("TriggerSubsystem.acquire_voltage_level_set", "TRIG:ACQ:VOLT:LEV", ResultKind.PARAM_WRITE, "TriggerSubsystem", "write", ("validated_payload",)),
    ("TriggerSubsystem.acquire_current_level_set", "TRIG:ACQ:CURR:LEV", ResultKind.PARAM_WRITE, "TriggerSubsystem", "write", ("validated_payload",)),
    ("InitiateSubsystem.continuous_arb_set", "INITiate:CONTinuous:ARB", ResultKind.PARAM_WRITE, "InitiateSubsystem", "write", ("validated_payload",)),
    ("InitiateSubsystem.continuous_acq_set", "INITiate:CONTinuous:ACQuire", ResultKind.PARAM_WRITE, "InitiateSubsystem", "write", ("validated_payload",)),
)
COMMAND_SPECS = MappingProxyType({
    **{m: CommandSpec(m, h, k, f, effect="write" if k is ResultKind.BOOL_WRITE else "unknown_read") for m, h, k, f in _ROWS},
    **{m: CommandSpec(m, h, k, f, effect=e) for m, h, k, f, e in _ADDITIONAL_ROWS},
    **{m: CommandSpec(m, h, k, f, effect=e, parameters=p) for m, h, k, f, e, p in _PARAMETERIZED_ROWS},
})


def command_spec(method: str) -> CommandSpec:
    try:
        return COMMAND_SPECS[method]
    except KeyError as exc:
        raise UnsupportedOperationError(f"no typed runtime specification for {method}") from exc


def execute(driver, method: str, *args):
    """Use the existing guarded driver I/O and shared core response parsers."""
    spec = command_spec(method)
    with driver._qualified_method_scope(method):
        return _execute(driver, spec, *args)


def _execute(driver, spec, *args):
    if spec.kind is ResultKind.BOOL_WRITE:
        if len(args) != 1:
            raise ConfigurationError("one boolean argument required")
        state = strict_bool(args[0])
        driver.write_scpi(spec.header + (" ON" if state else " OFF"))
        return None
    if args:
        raise ConfigurationError("scalar operation takes no command arguments")
    if spec.kind is ResultKind.VOID_WRITE:
        driver.write_scpi(spec.header)
        return None
    if spec.kind not in (ResultKind.FLOAT, ResultKind.BOOL, ResultKind.INT, ResultKind.RAW):
        raise UnsupportedOperationError("array operations require explicit format confirmation")
    raw = driver.query_scpi(spec.header)
    if spec.kind is ResultKind.RAW:
        return raw
    parser = {ResultKind.FLOAT: parse_float, ResultKind.BOOL: parse_bool, ResultKind.INT: parse_int}[spec.kind]
    return parser(raw)


def execute_parameterized(driver, method: str, payload: str):
    """Execute a fixed registered header with one already validated payload.

    Never accept multiple program messages or arbitrary headers. Per-command
    numeric, enum and hardware-envelope validation remains in typed methods.
    """
    spec = command_spec(method)
    if spec.kind not in (ResultKind.PARAM_WRITE, ResultKind.PARAM_QUERY):
        raise ConfigurationError("registered parameterized command required")
    if not isinstance(payload, str) or not payload or any(c in payload for c in ("\r", "\n", ";", "\x00")):
        raise ConfigurationError("invalid single-command argument payload")
    command = spec.header + " " + payload
    if spec.kind is ResultKind.PARAM_WRITE:
        driver.write_scpi(command)
        return None
    return driver.query_scpi(command)
