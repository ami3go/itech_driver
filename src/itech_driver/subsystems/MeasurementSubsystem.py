"""Fresh DC measurements, independent of programmed setpoints."""
from ._arrays import ascii_array_query, binary_array_query
from ..command_specs import execute, command_spec


class MeasurementSubsystem:
    def __init__(self, parent):
        self._p = parent

    def voltage_query(self) -> float:
        return execute(self._p, "MeasurementSubsystem.voltage_query")

    def voltage_high_query(self) -> float:
        return execute(self._p, "MeasurementSubsystem.voltage_high_query")

    def voltage_low_query(self) -> float:
        return execute(self._p, "MeasurementSubsystem.voltage_low_query")

    def voltage_max_query(self) -> float:
        return execute(self._p, "MeasurementSubsystem.voltage_max_query")

    def voltage_min_query(self) -> float:
        return execute(self._p, "MeasurementSubsystem.voltage_min_query")

    def current_query(self) -> float:
        return execute(self._p, "MeasurementSubsystem.current_query")

    def current_high_query(self) -> float:
        return execute(self._p, "MeasurementSubsystem.current_high_query")

    def current_low_query(self) -> float:
        return execute(self._p, "MeasurementSubsystem.current_low_query")

    def current_max_query(self) -> float:
        return execute(self._p, "MeasurementSubsystem.current_max_query")

    def current_min_query(self) -> float:
        return execute(self._p, "MeasurementSubsystem.current_min_query")

    def power_query(self) -> float:
        return execute(self._p, "MeasurementSubsystem.power_query")

    def power_max_query(self) -> float:
        return execute(self._p, "MeasurementSubsystem.power_max_query")

    def power_min_query(self) -> float:
        return execute(self._p, "MeasurementSubsystem.power_min_query")

    def voltage_array_query(self, *, ascii_confirmed: bool = False, expected_points: int | None = None) -> list[float]:
        return ascii_array_query(self._p, command_spec("MeasurementSubsystem.voltage_array_query").header, ascii_confirmed=ascii_confirmed, expected_points=expected_points)

    def current_array_query(self, *, ascii_confirmed: bool = False, expected_points: int | None = None) -> list[float]:
        return ascii_array_query(self._p, command_spec("MeasurementSubsystem.current_array_query").header, ascii_confirmed=ascii_confirmed, expected_points=expected_points)

    def power_array_query(self, *, ascii_confirmed: bool = False, expected_points: int | None = None) -> list[float]:
        return ascii_array_query(self._p, command_spec("MeasurementSubsystem.power_array_query").header, ascii_confirmed=ascii_confirmed, expected_points=expected_points)

    def voltage_binary_array_query(self, *, datatype: str, byte_order: str, expected_points: int,
                                   binary_confirmed: bool = False, consume_terminator: bool):
        return binary_array_query(self._p, command_spec("MeasurementSubsystem.voltage_binary_array_query").header, datatype=datatype,
                                  byte_order=byte_order, expected_points=expected_points,
                                  binary_confirmed=binary_confirmed, consume_terminator=consume_terminator)

    def current_binary_array_query(self, *, datatype: str, byte_order: str, expected_points: int,
                                   binary_confirmed: bool = False, consume_terminator: bool):
        return binary_array_query(self._p, command_spec("MeasurementSubsystem.current_binary_array_query").header, datatype=datatype,
                                  byte_order=byte_order, expected_points=expected_points,
                                  binary_confirmed=binary_confirmed, consume_terminator=consume_terminator)

    def power_binary_array_query(self, *, datatype: str, byte_order: str, expected_points: int,
                                   binary_confirmed: bool = False, consume_terminator: bool):
        return binary_array_query(self._p, command_spec("MeasurementSubsystem.power_binary_array_query").header, datatype=datatype,
                                  byte_order=byte_order, expected_points=expected_points,
                                  binary_confirmed=binary_confirmed, consume_terminator=consume_terminator)
