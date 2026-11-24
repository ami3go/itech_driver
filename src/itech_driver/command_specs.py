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

    @property
    def modifies_state(self) -> bool:
        return self.kind in (ResultKind.BOOL_WRITE, ResultKind.VOID_WRITE) or self.effect == "destructive_read"


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
COMMAND_SPECS = MappingProxyType({
    **{m: CommandSpec(m, h, k, f, effect="write" if k is ResultKind.BOOL_WRITE else "unknown_read") for m, h, k, f in _ROWS},
    **{m: CommandSpec(m, h, k, f, effect=e) for m, h, k, f, e in _ADDITIONAL_ROWS},
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
