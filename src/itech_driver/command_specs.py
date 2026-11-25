"""Typed command specifications for migrated runtime operations.

The inventory in docs/command_registry.json remains historical coverage.
A runtime spec establishes software wire syntax, not hardware qualification.
"""
from dataclasses import dataclass, replace
import re
from enum import Enum
from types import MappingProxyType

from scpi_driver_core import ConfigurationError, UnsupportedOperationError
from scpi_driver_core.scpi.parsers import parse_bool, parse_float, parse_int
from .utils.validation import strict_bool, finite_number, nonnegative_number


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
    RESTRICTED = "restricted"
    ALIAS = "alias"
    CORE = "core"
    COMPOUND = "compound"
    TEMPLATE = "template"
    QUALIFIED = "qualified"
    PLANNER = "planner"


class FieldKind(str, Enum):
    INTEGER = "integer"
    NUMBER = "finite_number"
    NONNEGATIVE = "nonnegative_number"
    TOKEN = "discrete_token"
    BOOL01 = "boolean_01"
    ONOFF = "boolean_onoff"


@dataclass(frozen=True)
class WireField:
    name: str
    kind: FieldKind

    def format(self, value):
        if self.kind is FieldKind.INTEGER:
            if type(value) is not int:
                raise ConfigurationError(f"{self.name} must be an exact integer")
        elif self.kind is FieldKind.NUMBER:
            finite_number(value, self.name)
        elif self.kind is FieldKind.NONNEGATIVE:
            nonnegative_number(value, self.name)
        elif self.kind is FieldKind.TOKEN:
            if not isinstance(value, str) or re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", value) is None:
                raise ConfigurationError(f"{self.name} must be a single discrete token")
        elif self.kind is FieldKind.BOOL01:
            return str(int(strict_bool(value, self.name)))
        elif self.kind is FieldKind.ONOFF:
            return "ON" if strict_bool(value, self.name) else "OFF"
        return str(value)


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
    dependencies: tuple[str, ...] = ()
    bound_selectors: tuple[str, ...] = ()
    unit: str | None = None
    fields: tuple[WireField, ...] = ()

    @property
    def modifies_state(self) -> bool:
        return self.kind in (ResultKind.BOOL_WRITE, ResultKind.VOID_WRITE, ResultKind.PARAM_WRITE) or self.effect in ("write", "destructive_read", "conditional")


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
# Explicit disposition for all other public inventory entries.
_FINAL_ROWS = (
    ("AbortSubsystem.dlog", "", ResultKind.RESTRICTED, "AbortSubsystem", "unavailable", (), ()),
    ("AbortSubsystem.elog", "", ResultKind.RESTRICTED, "AbortSubsystem", "unavailable", (), ()),
    ("ArbSubsystem.terminate_last_set", "", ResultKind.RESTRICTED, "ArbSubsystem", "unavailable", (), ()),
    ("ArbSubsystem.terminate_last_query", "", ResultKind.RESTRICTED, "ArbSubsystem", "unavailable", (), ()),
    ("BatterySubsystem.state_set", "", ResultKind.RESTRICTED, "BatterySubsystem", "unavailable", (), ()),
    ("BatterySubsystem.state_query", "", ResultKind.RESTRICTED, "BatterySubsystem", "unavailable", (), ()),
    ("SourceSubsystem.remote_sense_query", "", ResultKind.RESTRICTED, "SourceSubsystem", "unavailable", (), ()),
    ("SystemSubsystem.preset", "", ResultKind.RESTRICTED, "SystemSubsystem", "unavailable", (), ()),
    ("TriggerSubsystem.source_set", "", ResultKind.RESTRICTED, "TriggerSubsystem", "unavailable", (), ()),
    ("TriggerSubsystem.source_query", "", ResultKind.RESTRICTED, "TriggerSubsystem", "unavailable", (), ()),
    ("TriggerSubsystem.level_set", "", ResultKind.RESTRICTED, "TriggerSubsystem", "unavailable", (), ()),
    ("TriggerSubsystem.level_query", "", ResultKind.RESTRICTED, "TriggerSubsystem", "unavailable", (), ()),
    ("TriggerSubsystem.delay_set", "", ResultKind.RESTRICTED, "TriggerSubsystem", "unavailable", (), ()),
    ("TriggerSubsystem.delay_query", "", ResultKind.RESTRICTED, "TriggerSubsystem", "unavailable", (), ()),
    ("TriggerSubsystem.hysteresis_set", "", ResultKind.RESTRICTED, "TriggerSubsystem", "unavailable", (), ()),
    ("TriggerSubsystem.hysteresis_query", "", ResultKind.RESTRICTED, "TriggerSubsystem", "unavailable", (), ()),
    ("SenseSubsystem.acquisition_interval_query", "", ResultKind.RESTRICTED, "SenseSubsystem", "unavailable", (), ()),
    ("SenseSubsystem.acquisition_offset_query", "", ResultKind.RESTRICTED, "SenseSubsystem", "unavailable", (), ()),
    ("SenseSubsystem.acquisition_points_query", "", ResultKind.RESTRICTED, "SenseSubsystem", "unavailable", (), ()),
    ("ArbSubsystem.init", "", ResultKind.ALIAS, "ArbSubsystem", "delegated", (), ("InitiateSubsystem.arb",)),
    ("ArbSubsystem.abort", "", ResultKind.ALIAS, "ArbSubsystem", "delegated", (), ("AbortSubsystem.arb",)),
    ("SourceSubsystem.power_limit_set", "", ResultKind.ALIAS, "SourceSubsystem", "delegated", (), ("SourceSubsystem.opp_threshold_set",)),
    ("SourceSubsystem.power_limit_query", "", ResultKind.ALIAS, "SourceSubsystem", "delegated", (), ("SourceSubsystem.opp_threshold_query",)),
    ("SourceSubsystem.power_limit_enable", "", ResultKind.ALIAS, "SourceSubsystem", "delegated", (), ("SourceSubsystem.opp_enable",)),
    ("SourceSubsystem.power_limit_enable_query", "", ResultKind.ALIAS, "SourceSubsystem", "delegated", (), ("SourceSubsystem.opp_enable_query",)),
    ("SourceSubsystem.transient_mode_set", "", ResultKind.ALIAS, "SourceSubsystem", "delegated", (), ("SourceSubsystem.function_mode_set",)),
    ("SourceSubsystem.transient_mode_query", "", ResultKind.ALIAS, "SourceSubsystem", "delegated", (), ("SourceSubsystem.function_mode_query",)),
    ("IEEE488.idn", "*IDN?", ResultKind.CORE, "IEEE488", "read", (), ()),
    ("IEEE488.reset", "*RST", ResultKind.CORE, "IEEE488", "write", (), ()),
    ("IEEE488.clear_status", "*CLS", ResultKind.CORE, "IEEE488", "write", (), ()),
    ("IEEE488.opc", "*OPC / *OPC?", ResultKind.CORE, "IEEE488", "conditional", ("wait:bool",), ()),
    ("IEEE488.self_test", "*TST?", ResultKind.CORE, "IEEE488", "unknown_read", (), ()),
    ("IEEE488.trigger", "*TRG", ResultKind.CORE, "IEEE488", "write", (), ()),
    ("IEEE488.save", "*SAV", ResultKind.CORE, "IEEE488", "write", ("slot:int",), ()),
    ("IEEE488.recall", "*RCL", ResultKind.CORE, "IEEE488", "write", ("slot:int",), ()),
    ("StatusSubsystem.std_event_enable_set", "*ESE", ResultKind.CORE, "StatusSubsystem", "write", ("mask:uint8",), ()),
    ("StatusSubsystem.std_event_enable_query", "*ESE?", ResultKind.CORE, "StatusSubsystem", "read", (), ()),
    ("StatusSubsystem.std_event_register_query", "*ESR?", ResultKind.CORE, "StatusSubsystem", "destructive_read", (), ()),
    ("StatusSubsystem.status_byte", "*STB?", ResultKind.CORE, "StatusSubsystem", "read", (), ()),
    ("ArbSubsystem.trigger", "TRIGger:ARB", ResultKind.VOID_WRITE, "ArbSubsystem", "write", (), ()),
    ("SourceSubsystem.ovp_set", "SOUR:VOLT:OVER:PROT:LEV", ResultKind.QUALIFIED, "SourceSubsystem", "write", ("value:finite_number","qualification:ProtectionThresholdQualification",), ()),
    ("SourceSubsystem.ovp_query", "SOUR:VOLT:OVER:PROT:LEV?", ResultKind.FLOAT, "SourceSubsystem", "read", (), ()),
    ("SourceSubsystem.ocp_set", "SOUR:CURR:OVER:PROT:LEV", ResultKind.QUALIFIED, "SourceSubsystem", "write", ("value:finite_number","qualification:ProtectionThresholdQualification",), ()),
    ("SourceSubsystem.ocp_query", "SOUR:CURR:OVER:PROT:LEV?", ResultKind.FLOAT, "SourceSubsystem", "read", (), ()),
    ("SourceSubsystem.opp_threshold_set", "SOUR:POW:OVER:PROT:LEV", ResultKind.QUALIFIED, "SourceSubsystem", "write", ("value:finite_number","qualification:ProtectionThresholdQualification",), ()),
    ("SourceSubsystem.opp_threshold_query", "SOUR:POW:OVER:PROT:LEV?", ResultKind.FLOAT, "SourceSubsystem", "read", (), ()),
    ("SourceSubsystem.uvp_set", "SOUR:VOLT:UND:PROT:LEV", ResultKind.QUALIFIED, "SourceSubsystem", "write", ("value:finite_number","qualification:ProtectionThresholdQualification",), ()),
    ("SourceSubsystem.uvp_query", "SOUR:VOLT:UND:PROT:LEV?", ResultKind.FLOAT, "SourceSubsystem", "read", (), ()),
    ("SourceSubsystem.ucp_set", "SOUR:CURR:UND:PROT:LEV", ResultKind.QUALIFIED, "SourceSubsystem", "write", ("value:finite_number","qualification:ProtectionThresholdQualification",), ()),
    ("SourceSubsystem.ucp_query", "SOUR:CURR:UND:PROT:LEV?", ResultKind.FLOAT, "SourceSubsystem", "read", (), ()),
    ("SourceSubsystem.ovp_enable_query", "SOUR:VOLT:OVER:PROT:STAT?", ResultKind.BOOL, "SourceSubsystem", "read", (), ()),
    ("SourceSubsystem.ocp_enable_query", "SOUR:CURR:OVER:PROT:STAT?", ResultKind.BOOL, "SourceSubsystem", "read", (), ()),
    ("SourceSubsystem.external_programming_set", "SOUR:EXT:PROG", ResultKind.COMPOUND, "SourceSubsystem", "write", ("enabled:bool",), ("OutputSubsystem.state_query",)),
    ("SourceSubsystem.external_coefficient_set", "SOUR:EXT:PROG:CHAN:{coefficient}", ResultKind.COMPOUND, "SourceSubsystem", "write", ("channel:int","coefficient:MX|MB","value:finite_number",), ("OutputSubsystem.state_query","SourceSubsystem.external_programming_query",)),
    ("SourceSubsystem.external_coefficient_query", "SOUR:EXT:PROG:CHAN:{coefficient}?", ResultKind.TEMPLATE, "SourceSubsystem", "read", ("channel:int","coefficient:MX|MB",), ()),
    ("OutputSubsystem.watchdog_set", "", ResultKind.COMPOUND, "OutputSubsystem", "write", ("enable:bool","delay_s:int|None",), ("OutputSubsystem.watchdog_query","OutputSubsystem.watchdog_delay_query",)),
    ("TriggerSubsystem.acquire_source_set", "TRIG:ACQ:SOUR", ResultKind.PARAM_WRITE, "TriggerSubsystem", "write", ("validated_payload",), ()),
    ("TriggerSubsystem.acquire_source_query", "TRIG:ACQ:SOUR?", ResultKind.RAW, "TriggerSubsystem", "read", (), ()),
    ("TriggerSubsystem.arb_source_set", "TRIG:ARB:SOUR", ResultKind.PARAM_WRITE, "TriggerSubsystem", "write", ("validated_payload",), ()),
    ("TriggerSubsystem.arb_source_query", "TRIG:ARB:SOUR?", ResultKind.RAW, "TriggerSubsystem", "read", (), ()),
    ("TriggerSubsystem.dlog_source_set", "TRIG:DLOG:SOUR", ResultKind.PARAM_WRITE, "TriggerSubsystem", "write", ("validated_payload",), ()),
    ("TriggerSubsystem.dlog_source_query", "TRIG:DLOG:SOUR?", ResultKind.RAW, "TriggerSubsystem", "read", (), ()),
    ("TriggerSubsystem.elog_source_set", "TRIG:ELOG:SOUR", ResultKind.PARAM_WRITE, "TriggerSubsystem", "write", ("validated_payload",), ()),
    ("TriggerSubsystem.elog_source_query", "TRIG:ELOG:SOUR?", ResultKind.RAW, "TriggerSubsystem", "read", (), ()),
    ("TriggerSubsystem.acquire_start", "", ResultKind.COMPOUND, "TriggerSubsystem", "write", ("source:enum",), ("TriggerSubsystem.acquire_source_set","TriggerSubsystem.acquire_arm",)),
    ("TriggerSubsystem.hysteresis_threshold_query", "TRIG:{subsystem}:{quantity}:HYST:{bound}?", ResultKind.TEMPLATE, "TriggerSubsystem", "read", ("subsystem:ACQ|DLOG|ELOG","quantity:VOLT|CURR","bound:HIGH|LOW",), ()),
    ("TriggerSubsystem.hysteresis_threshold_set", "TRIG:{subsystem}:{quantity}:HYST:{bound}", ResultKind.COMPOUND, "TriggerSubsystem", "write", ("subsystem:enum","quantity:enum","bound:enum","value:finite_number",), ("TriggerSubsystem.hysteresis_threshold_query",)),
    ("TriggerSubsystem.elog_trigger_voltage_high_set", "", ResultKind.ALIAS, "TriggerSubsystem", "delegated", ("value:finite_number",), ("TriggerSubsystem.hysteresis_threshold_set",)),
    ("TriggerSubsystem.elog_trigger_voltage_low_set", "", ResultKind.ALIAS, "TriggerSubsystem", "delegated", ("value:finite_number",), ("TriggerSubsystem.hysteresis_threshold_set",)),
    ("LoggingSubsystem.commands", "", ResultKind.PLANNER, "LoggingSubsystem", "none", ("kind:ELOG|DLOG","min_period:finite_number","max_period:finite_number","max_duration:finite_number",), ()),
    ("LoggingSubsystem.raw_data_query", "FETC:ELOG:ARR:DATA?", ResultKind.TEMPLATE, "LoggingSubsystem", "read", ("ascii_confirmed:bool",), ()),
    ("LoggingSubsystem.state_query", "{kind}:STAT?", ResultKind.TEMPLATE, "LoggingSubsystem", "read", ("kind:ELOG|DLOG",), ()),
)

LOGGING_CONFIG_TEMPLATES = (
    "SENS:{kind}:FUNC:VOLT {value}", "SENS:{kind}:FUNC:CURR {value}",
    "SENS:{kind}:FUNC:PEAK {value}", "SENS:{kind}:PER {value}", "SENS:{kind}:TIME {value}",
)
_BASE_COMMAND_SPECS = {
    **{m: CommandSpec(m, h, k, f, effect="write" if k is ResultKind.BOOL_WRITE else "unknown_read") for m, h, k, f in _ROWS},
    **{m: CommandSpec(m, h, k, f, effect=e) for m, h, k, f, e in _ADDITIONAL_ROWS},
    **{m: CommandSpec(m, h, k, f, effect=e, parameters=p) for m, h, k, f, e, p in _PARAMETERIZED_ROWS},
    **{m: CommandSpec(m, h, k, f, effect=e, parameters=p, dependencies=d) for m, h, k, f, e, p, d in _FINAL_ROWS},
}

_WIRE_FIELDS = MappingProxyType({
    "ArbSubsystem.function_shape_set": (WireField("shape", FieldKind.TOKEN),),
    "ArbSubsystem.function_type_set": (WireField("type", FieldKind.TOKEN),),
    "ArbSubsystem.udef_count_set": (WireField("steps", FieldKind.INTEGER),),
    "ArbSubsystem.count_set": (WireField("cnt", FieldKind.INTEGER),),
    "ArbSubsystem.save": (WireField("index", FieldKind.INTEGER),),
    "ArbSubsystem.recall": (WireField("index", FieldKind.INTEGER),),
    "ArbSubsystem.udef_level_set": (WireField("step", FieldKind.INTEGER), WireField("level", FieldKind.NUMBER),),
    "ArbSubsystem.udef_level_query": (WireField("step", FieldKind.INTEGER),),
    "ArbSubsystem.udef_dwell_set": (WireField("step", FieldKind.INTEGER), WireField("seconds", FieldKind.NUMBER),),
    "ArbSubsystem.udef_dwell_query": (WireField("step", FieldKind.INTEGER),),
    "ArbSubsystem.udef_slew_set": (WireField("step", FieldKind.INTEGER), WireField("slew_val", FieldKind.NUMBER),),
    "ArbSubsystem.udef_slew_query": (WireField("step", FieldKind.INTEGER),),
    "ArbSubsystem.pause_set": (WireField("enable", FieldKind.BOOL01),),
    "SourceSubsystem.function_set": (WireField("mode", FieldKind.TOKEN),),
    "SourceSubsystem.function_mode_set": (WireField("mode", FieldKind.TOKEN),),
    "SourceSubsystem.ovp_enable": (WireField("enable", FieldKind.BOOL01),),
    "SourceSubsystem.ocp_enable": (WireField("enable", FieldKind.BOOL01),),
    "SourceSubsystem.opp_enable": (WireField("enable", FieldKind.BOOL01),),
    "SourceSubsystem.remote_sense_set": (WireField("enable", FieldKind.BOOL01),),
    "SourceSubsystem.uvp_enable": (WireField("enable", FieldKind.BOOL01),),
    "SourceSubsystem.ucp_enable": (WireField("enable", FieldKind.BOOL01),),
    "SourceSubsystem.cv_loop_speed_set": (WireField("speed", FieldKind.TOKEN),),
    "SourceSubsystem.cc_loop_speed_set": (WireField("speed", FieldKind.TOKEN),),
    "IOConfigSubsystem.select": (WireField("pin", FieldKind.INTEGER),),
    "IOConfigSubsystem.direction_set": (WireField("pin", FieldKind.INTEGER), WireField("direction", FieldKind.BOOL01),),
    "IOConfigSubsystem.direction_query": (WireField("pin", FieldKind.INTEGER),),
    "IOConfigSubsystem.pwm_enable": (WireField("pin", FieldKind.INTEGER), WireField("enable", FieldKind.BOOL01),),
    "IOConfigSubsystem.pwm_freq_set": (WireField("pin", FieldKind.INTEGER), WireField("frequency", FieldKind.NONNEGATIVE),),
    "IOConfigSubsystem.pwm_duty_set": (WireField("pin", FieldKind.INTEGER), WireField("duty_percent", FieldKind.INTEGER),),
    "IOConfigSubsystem.reverse_set": (WireField("pin", FieldKind.INTEGER), WireField("enabled", FieldKind.BOOL01),),
    "IOConfigSubsystem.reverse_query": (WireField("pin", FieldKind.INTEGER),),
    "IOConfigSubsystem.pwm_enable_query": (WireField("pin", FieldKind.INTEGER),),
    "IOConfigSubsystem.pwm_duty_query": (WireField("pin", FieldKind.INTEGER),),
    "IOConfigSubsystem.pulse_width_set": (WireField("pin", FieldKind.INTEGER), WireField("seconds", FieldKind.NONNEGATIVE),),
    "IOConfigSubsystem.pin_function_set": (WireField("pin", FieldKind.INTEGER), WireField("function", FieldKind.TOKEN),),
    "IOConfigSubsystem.pin_function_query": (WireField("pin", FieldKind.INTEGER),),
    "IOConfigSubsystem.output_level_set": (WireField("pin", FieldKind.INTEGER), WireField("high", FieldKind.BOOL01),),
    "SenseSubsystem.acquisition_points_set": (WireField("points", FieldKind.INTEGER),),
    "SenseSubsystem.acquisition_offset_set": (WireField("points", FieldKind.INTEGER),),
    "SenseSubsystem.acquisition_interval_set": (WireField("interval", FieldKind.NUMBER),),
    "BatterySubsystem.charge_voltage_set": (WireField("volts", FieldKind.NONNEGATIVE),),
    "BatterySubsystem.charge_current_set": (WireField("amps", FieldKind.NONNEGATIVE),),
    "BatterySubsystem.shutdown_voltage_set": (WireField("volts", FieldKind.NONNEGATIVE),),
    "BatterySubsystem.shutdown_current_set": (WireField("amps", FieldKind.NONNEGATIVE),),
    "BatterySubsystem.shutdown_capacity_set": (WireField("ah", FieldKind.NONNEGATIVE),),
    "BatterySubsystem.shutdown_time_set": (WireField("seconds", FieldKind.NONNEGATIVE),),
    "OutputSubsystem.delay_rise_set": (WireField("seconds", FieldKind.NONNEGATIVE),),
    "OutputSubsystem.delay_fall_set": (WireField("seconds", FieldKind.NONNEGATIVE),),
    "OutputSubsystem.inhibit_mode_set": (WireField("mode", FieldKind.TOKEN),),
    "OutputSubsystem.power_on_mode_set": (WireField("mode", FieldKind.TOKEN),),
    "SystemSubsystem.beeper_state_set": (WireField("on", FieldKind.ONOFF),),
    "SystemSubsystem.date_set": (WireField("year", FieldKind.INTEGER), WireField("month", FieldKind.INTEGER), WireField("day", FieldKind.INTEGER),),
    "SystemSubsystem.time_set": (WireField("hour", FieldKind.INTEGER), WireField("minute", FieldKind.INTEGER), WireField("second", FieldKind.INTEGER),),
    "SystemSubsystem.comm_select": (WireField("interface", FieldKind.TOKEN),),
    "SystemSubsystem.comm_gpib_addr_set": (WireField("address", FieldKind.INTEGER),),
    "SystemSubsystem.lan_ip_mode_set": (WireField("mode", FieldKind.TOKEN),),
    "TriggerSubsystem.acquire_mode_set": (WireField("mode", FieldKind.TOKEN),),
    "TriggerSubsystem.acquire_voltage_level_set": (WireField("value", FieldKind.NONNEGATIVE),),
    "TriggerSubsystem.acquire_current_level_set": (WireField("value", FieldKind.NONNEGATIVE),),
    "TriggerSubsystem.acquire_source_set": (WireField("source", FieldKind.TOKEN),),
    "TriggerSubsystem.arb_source_set": (WireField("source", FieldKind.TOKEN),),
    "TriggerSubsystem.dlog_source_set": (WireField("source", FieldKind.TOKEN),),
    "TriggerSubsystem.elog_source_set": (WireField("source", FieldKind.TOKEN),),
    "InitiateSubsystem.continuous_arb_set": (WireField("enable", FieldKind.BOOL01),),
    "InitiateSubsystem.continuous_acq_set": (WireField("enable", FieldKind.BOOL01),),
})
_TYPED_COMMAND_SPECS = MappingProxyType({
    method: replace(spec, fields=_WIRE_FIELDS[method],
                    parameters=tuple(f"{field.name}:{field.kind.value}" for field in _WIRE_FIELDS[method]))
    if method in _WIRE_FIELDS else spec
    for method, spec in _BASE_COMMAND_SPECS.items()
})

# Imported from the checked-in guide-index evidence inventory, not HIL proof.
_GUIDE_INDEX_PAGES = MappingProxyType({
    "OutputSubsystem.state_set": 93,
    "OutputSubsystem.state_query": 94,
    "SourceSubsystem.voltage_set": 57,
    "SourceSubsystem.voltage_query": 58,
    "SourceSubsystem.current_set": 38,
    "SourceSubsystem.current_query": 39,
    "SourceSubsystem.output_power_limit_set": 76,
    "SourceSubsystem.output_power_limit_query": 77,
    "SourceSubsystem.voltage_limit_set": 75,
    "SourceSubsystem.voltage_limit_query": 76,
    "SourceSubsystem.current_limit_set": 56,
    "SourceSubsystem.current_limit_query": 56,
    "SourceSubsystem.programmed_power_limit_set": 76,
    "SourceSubsystem.programmed_power_limit_query": 77,
    "SourceSubsystem.ovp_delay_set": 67,
    "SourceSubsystem.ovp_delay_query": 68,
    "SourceSubsystem.ocp_delay_set": 48,
    "SourceSubsystem.ocp_delay_query": 48,
    "SourceSubsystem.opp_delay_set": 81,
    "SourceSubsystem.opp_delay_query": 82,
    "SourceSubsystem.uvp_delay_set": 71,
    "SourceSubsystem.uvp_delay_query": 72,
    "SourceSubsystem.ucp_delay_set": 52,
    "SourceSubsystem.ucp_delay_query": 53,
    "SourceSubsystem.uvp_warmup_set": 73,
    "SourceSubsystem.uvp_warmup_query": 74,
    "SourceSubsystem.ucp_warmup_set": 54,
    "SourceSubsystem.ucp_warmup_query": 55,
    "SourceSubsystem.voltage_rise_time_set": 60,
    "SourceSubsystem.voltage_rise_time_query": 61,
    "SourceSubsystem.voltage_fall_time_set": 62,
    "SourceSubsystem.voltage_fall_time_query": 63,
    "SourceSubsystem.voltage_both_time_set": 59,
    "SourceSubsystem.voltage_both_time_query": 60,
    "SourceSubsystem.current_rise_time_set": 41,
    "SourceSubsystem.current_rise_time_query": 42,
    "SourceSubsystem.current_fall_time_set": 43,
    "SourceSubsystem.current_fall_time_query": 44,
    "SourceSubsystem.current_both_time_set": 40,
    "SourceSubsystem.current_both_time_query": 41,
    "SourceSubsystem.resistance_set": 83,
    "SourceSubsystem.resistance_query": 84,
    "SourceSubsystem.ovp_set": 65,
    "SourceSubsystem.ovp_query": 66,
    "SourceSubsystem.ocp_set": 46,
    "SourceSubsystem.ocp_query": 47,
    "SourceSubsystem.opp_threshold_set": 80,
    "SourceSubsystem.opp_threshold_query": 80,
    "SourceSubsystem.uvp_set": 70,
    "SourceSubsystem.uvp_query": 71,
    "SourceSubsystem.ucp_set": 51,
    "SourceSubsystem.ucp_query": 52,
})
# A setter that reads live bounds depends on the matching qualified query.
_RANGE_READ_DEPENDENCIES = MappingProxyType({
    "SourceSubsystem.voltage_set": ("SourceSubsystem.voltage_query",),
    "SourceSubsystem.current_set": ("SourceSubsystem.current_query",),
    "SourceSubsystem.output_power_limit_set": ("SourceSubsystem.output_power_limit_query",),
    "SourceSubsystem.voltage_limit_set": ("SourceSubsystem.voltage_limit_query",),
    "SourceSubsystem.current_limit_set": ("SourceSubsystem.current_limit_query",),
    "SourceSubsystem.programmed_power_limit_set": ("SourceSubsystem.programmed_power_limit_query",),
    "SourceSubsystem.ovp_delay_set": ("SourceSubsystem.ovp_delay_query",),
    "SourceSubsystem.ocp_delay_set": ("SourceSubsystem.ocp_delay_query",),
    "SourceSubsystem.opp_delay_set": ("SourceSubsystem.opp_delay_query",),
    "SourceSubsystem.uvp_delay_set": ("SourceSubsystem.uvp_delay_query",),
    "SourceSubsystem.ucp_delay_set": ("SourceSubsystem.ucp_delay_query",),
    "SourceSubsystem.uvp_warmup_set": ("SourceSubsystem.uvp_warmup_query",),
    "SourceSubsystem.ucp_warmup_set": ("SourceSubsystem.ucp_warmup_query",),
    "SourceSubsystem.voltage_rise_time_set": ("SourceSubsystem.voltage_rise_time_query",),
    "SourceSubsystem.voltage_fall_time_set": ("SourceSubsystem.voltage_fall_time_query",),
    "SourceSubsystem.voltage_both_time_set": ("SourceSubsystem.voltage_both_time_query",),
    "SourceSubsystem.current_rise_time_set": ("SourceSubsystem.current_rise_time_query",),
    "SourceSubsystem.current_fall_time_set": ("SourceSubsystem.current_fall_time_query",),
    "SourceSubsystem.current_both_time_set": ("SourceSubsystem.current_both_time_query",),
    "SourceSubsystem.resistance_set": ("SourceSubsystem.resistance_query", "SourceSubsystem.function_query",),
})
_RANGE_AWARE_COMMAND_SPECS = MappingProxyType({
    method: replace(spec, dependencies=_RANGE_READ_DEPENDENCIES[method])
    if method in _RANGE_READ_DEPENDENCIES else spec
    for method, spec in _TYPED_COMMAND_SPECS.items()
})
# IT-M3900D programming guide V1.4/09,2024, part 402225, source index pp. IX–X.
# These are syntax attestations, not numerical ranges or firmware qualification.
_SOURCE_BOUND_QUERY_KEYS = frozenset((
    "SourceSubsystem.voltage_query",
    "SourceSubsystem.current_query",
    "SourceSubsystem.output_power_limit_query",
    "SourceSubsystem.voltage_limit_query",
    "SourceSubsystem.current_limit_query",
    "SourceSubsystem.programmed_power_limit_query",
    "SourceSubsystem.ovp_delay_query",
    "SourceSubsystem.ocp_delay_query",
    "SourceSubsystem.opp_delay_query",
    "SourceSubsystem.uvp_delay_query",
    "SourceSubsystem.ucp_delay_query",
    "SourceSubsystem.uvp_warmup_query",
    "SourceSubsystem.ucp_warmup_query",
    "SourceSubsystem.voltage_rise_time_query",
    "SourceSubsystem.voltage_fall_time_query",
    "SourceSubsystem.voltage_both_time_query",
    "SourceSubsystem.current_rise_time_query",
    "SourceSubsystem.current_fall_time_query",
    "SourceSubsystem.current_both_time_query",
    "SourceSubsystem.resistance_query",
))
_SOURCE_UNITS = MappingProxyType({
    "SourceSubsystem.voltage_set": "V",
    "SourceSubsystem.voltage_query": "V",
    "SourceSubsystem.current_set": "A",
    "SourceSubsystem.current_query": "A",
    "SourceSubsystem.output_power_limit_set": "W",
    "SourceSubsystem.output_power_limit_query": "W",
    "SourceSubsystem.voltage_limit_set": "V",
    "SourceSubsystem.voltage_limit_query": "V",
    "SourceSubsystem.current_limit_set": "A",
    "SourceSubsystem.current_limit_query": "A",
    "SourceSubsystem.programmed_power_limit_set": "W",
    "SourceSubsystem.programmed_power_limit_query": "W",
    "SourceSubsystem.ovp_delay_set": "s",
    "SourceSubsystem.ovp_delay_query": "s",
    "SourceSubsystem.ocp_delay_set": "s",
    "SourceSubsystem.ocp_delay_query": "s",
    "SourceSubsystem.opp_delay_set": "s",
    "SourceSubsystem.opp_delay_query": "s",
    "SourceSubsystem.uvp_delay_set": "s",
    "SourceSubsystem.uvp_delay_query": "s",
    "SourceSubsystem.ucp_delay_set": "s",
    "SourceSubsystem.ucp_delay_query": "s",
    "SourceSubsystem.uvp_warmup_set": "s",
    "SourceSubsystem.uvp_warmup_query": "s",
    "SourceSubsystem.ucp_warmup_set": "s",
    "SourceSubsystem.ucp_warmup_query": "s",
    "SourceSubsystem.voltage_rise_time_set": "s",
    "SourceSubsystem.voltage_rise_time_query": "s",
    "SourceSubsystem.voltage_fall_time_set": "s",
    "SourceSubsystem.voltage_fall_time_query": "s",
    "SourceSubsystem.voltage_both_time_set": "s",
    "SourceSubsystem.voltage_both_time_query": "s",
    "SourceSubsystem.current_rise_time_set": "s",
    "SourceSubsystem.current_rise_time_query": "s",
    "SourceSubsystem.current_fall_time_set": "s",
    "SourceSubsystem.current_fall_time_query": "s",
    "SourceSubsystem.current_both_time_set": "s",
    "SourceSubsystem.current_both_time_query": "s",
    "SourceSubsystem.resistance_set": "ohm",
    "SourceSubsystem.resistance_query": "ohm",
    "SourceSubsystem.ovp_set": "V",
    "SourceSubsystem.ovp_query": "V",
    "SourceSubsystem.ocp_set": "A",
    "SourceSubsystem.ocp_query": "A",
    "SourceSubsystem.opp_threshold_set": "W",
    "SourceSubsystem.opp_threshold_query": "W",
    "SourceSubsystem.uvp_set": "V",
    "SourceSubsystem.uvp_query": "V",
    "SourceSubsystem.ucp_set": "A",
    "SourceSubsystem.ucp_query": "A",
})
_SOURCE_METADATA_SPECS = MappingProxyType({
    method: replace(spec, unit=_SOURCE_UNITS[method],
                    bound_selectors=("MIN", "MAX", "DEF") if method in _SOURCE_BOUND_QUERY_KEYS else ())
    if method in _SOURCE_UNITS else spec
    for method, spec in _RANGE_AWARE_COMMAND_SPECS.items()
})
COMMAND_SPECS = MappingProxyType({
    method: replace(spec, guide_status="indexed_text_reference", guide_page=_GUIDE_INDEX_PAGES[method])
    if method in _GUIDE_INDEX_PAGES else spec
    for method, spec in _SOURCE_METADATA_SPECS.items()
})


def command_spec(method: str) -> CommandSpec:
    try:
        return COMMAND_SPECS[method]
    except KeyError as exc:
        raise UnsupportedOperationError(f"no typed runtime specification for {method}") from exc


def source_bound_command(method: str, bound=None) -> str:
    """Render only guide-indexed source range queries; never probe thresholds."""
    spec = command_spec(method)
    if not spec.bound_selectors:
        raise UnsupportedOperationError(f"no documented source range selectors for {method}")
    if bound is not None and (not isinstance(bound, str) or bound not in spec.bound_selectors):
        raise ConfigurationError("bound must be MIN, MAX, DEF or None")
    return spec.header.removesuffix("?") + "?" + ("" if bound is None else " " + bound)


def execute_source_bound(driver, method: str, bound=None) -> float:
    command = source_bound_command(method, bound)
    with driver._qualified_method_scope(method):
        return parse_float(driver.query_scpi(command))


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


def execute_parameterized(driver, method: str, *values):
    """Render individual typed wire fields; subsystem validators own ranges.

    This is an internal transport helper, not a substitute for the public
    method's model, application, channel or compound preconditions.
    """
    spec = command_spec(method)
    if spec.kind not in (ResultKind.PARAM_WRITE, ResultKind.PARAM_QUERY):
        raise ConfigurationError("registered parameterized command required")
    if len(values) != len(spec.fields):
        raise ConfigurationError(f"{method} requires {len(spec.fields)} wire arguments")
    payload = ",".join(field.format(value) for field, value in zip(spec.fields, values))
    command = spec.header + " " + payload
    with driver._qualified_method_scope(method):
        # Exact integer fields alone do not enforce the ARB command envelope.
        # Local import avoids the registry/capabilities initialization cycle.
        if method.startswith("ArbSubsystem."):
            from .arb_integer_qualification import FAMILY_INTEGER_MAX, validate_arb_integer
            operation = method.split(".", 1)[1]
            if operation in FAMILY_INTEGER_MAX:
                validate_arb_integer(driver, operation, values[0])
        if spec.kind is ResultKind.PARAM_WRITE:
            driver.write_scpi(command)
            return None
        return driver.query_scpi(command)
