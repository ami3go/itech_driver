"""Typed command specifications for migrated runtime operations.

The inventory in docs/command_registry.json remains historical coverage.
A runtime spec establishes software wire syntax, not hardware qualification.
"""
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

from scpi_driver_core import ConfigurationError, UnsupportedOperationError
from scpi_driver_core.scpi.parsers import parse_bool, parse_float
from .utils.validation import strict_bool


class ResultKind(str, Enum):
    FLOAT = "float"
    BOOL = "bool"
    ASCII_ARRAY = "ascii_array"
    BINARY_ARRAY = "binary_array"
    BOOL_WRITE = "bool_write"


@dataclass(frozen=True)
class CommandSpec:
    method: str
    header: str
    kind: ResultKind
    feature: str
    guide_status: str = "unverified"
    guide_page: int | None = None
    replay: str = "never"

    @property
    def modifies_state(self) -> bool:
        return self.kind is ResultKind.BOOL_WRITE


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
COMMAND_SPECS = MappingProxyType({m: CommandSpec(m, h, k, f) for m, h, k, f in _ROWS})


def command_spec(method: str) -> CommandSpec:
    try:
        return COMMAND_SPECS[method]
    except KeyError as exc:
        raise UnsupportedOperationError(f"no typed runtime specification for {method}") from exc


def execute(driver, method: str, *args):
    """Use the existing guarded driver I/O and shared core response parsers."""
    spec = command_spec(method)
    if spec.kind is ResultKind.BOOL_WRITE:
        if len(args) != 1:
            raise ConfigurationError("one boolean argument required")
        state = strict_bool(args[0])
        driver.write_scpi(spec.header + (" ON" if state else " OFF"))
        return None
    if args:
        raise ConfigurationError("scalar query takes no command arguments")
    if spec.kind not in (ResultKind.FLOAT, ResultKind.BOOL):
        raise UnsupportedOperationError("array operations require explicit format confirmation")
    raw = driver.query_scpi(spec.header)
    return parse_float(raw) if spec.kind is ResultKind.FLOAT else parse_bool(raw)
