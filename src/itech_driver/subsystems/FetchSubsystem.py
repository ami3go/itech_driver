"""Retrieve buffered data without arming or triggering a fresh acquisition.

The caller is responsible for acquisition completion and freshness. A successful
fetch alone does not establish that data belongs to the latest acquisition.
"""
from ..command_specs import execute, command_spec
from ._arrays import ascii_array_query, binary_array_query


class FetchSubsystem:
    def __init__(self, parent):
        self._p = parent

    def voltage_query(self) -> float:
        return execute(self._p, "FetchSubsystem.voltage_query")

    def voltage_high_query(self) -> float:
        return execute(self._p, "FetchSubsystem.voltage_high_query")

    def voltage_low_query(self) -> float:
        return execute(self._p, "FetchSubsystem.voltage_low_query")

    def voltage_max_query(self) -> float:
        return execute(self._p, "FetchSubsystem.voltage_max_query")

    def voltage_min_query(self) -> float:
        return execute(self._p, "FetchSubsystem.voltage_min_query")

    def current_query(self) -> float:
        return execute(self._p, "FetchSubsystem.current_query")

    def current_high_query(self) -> float:
        return execute(self._p, "FetchSubsystem.current_high_query")

    def current_low_query(self) -> float:
        return execute(self._p, "FetchSubsystem.current_low_query")

    def current_max_query(self) -> float:
        return execute(self._p, "FetchSubsystem.current_max_query")

    def current_min_query(self) -> float:
        return execute(self._p, "FetchSubsystem.current_min_query")

    def power_query(self) -> float:
        return execute(self._p, "FetchSubsystem.power_query")

    def power_max_query(self) -> float:
        return execute(self._p, "FetchSubsystem.power_max_query")

    def power_min_query(self) -> float:
        return execute(self._p, "FetchSubsystem.power_min_query")

    def voltage_array_query(self, *, ascii_confirmed: bool = False, expected_points: int | None = None) -> list[float]:
        return ascii_array_query(self._p, command_spec("FetchSubsystem.voltage_array_query").header, ascii_confirmed=ascii_confirmed, expected_points=expected_points)

    def current_array_query(self, *, ascii_confirmed: bool = False, expected_points: int | None = None) -> list[float]:
        return ascii_array_query(self._p, command_spec("FetchSubsystem.current_array_query").header, ascii_confirmed=ascii_confirmed, expected_points=expected_points)

    def power_array_query(self, *, ascii_confirmed: bool = False, expected_points: int | None = None) -> list[float]:
        return ascii_array_query(self._p, command_spec("FetchSubsystem.power_array_query").header, ascii_confirmed=ascii_confirmed, expected_points=expected_points)

    def voltage_binary_array_query(self, *, datatype: str, byte_order: str, expected_points: int,
                                   binary_confirmed: bool = False, consume_terminator: bool):
        return binary_array_query(self._p, command_spec("FetchSubsystem.voltage_binary_array_query").header, datatype=datatype,
                                  byte_order=byte_order, expected_points=expected_points,
                                  binary_confirmed=binary_confirmed, consume_terminator=consume_terminator)

    def current_binary_array_query(self, *, datatype: str, byte_order: str, expected_points: int,
                                   binary_confirmed: bool = False, consume_terminator: bool):
        return binary_array_query(self._p, command_spec("FetchSubsystem.current_binary_array_query").header, datatype=datatype,
                                  byte_order=byte_order, expected_points=expected_points,
                                  binary_confirmed=binary_confirmed, consume_terminator=consume_terminator)

    def power_binary_array_query(self, *, datatype: str, byte_order: str, expected_points: int,
                                   binary_confirmed: bool = False, consume_terminator: bool):
        return binary_array_query(self._p, command_spec("FetchSubsystem.power_binary_array_query").header, datatype=datatype,
                                  byte_order=byte_order, expected_points=expected_points,
                                  binary_confirmed=binary_confirmed, consume_terminator=consume_terminator)
