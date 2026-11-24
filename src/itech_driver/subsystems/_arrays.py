from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.scpi.parsers import parse_float


def ascii_array_query(parent, header: str, *, ascii_confirmed: bool, expected_points: int | None) -> list[float]:
    if ascii_confirmed is not True:
        raise ConfigurationError("confirm instrument ASCII data format before array query")
    if expected_points is not None and (type(expected_points) is not int or expected_points <= 0):
        raise ConfigurationError("expected_points must be a positive integer")
    raw = parent.query_scpi(header)
    if not raw.strip() or any(not item.strip() for item in raw.split(",")):
        raise ResponseParseError("empty or incomplete measurement array", raw=raw)
    result = [parse_float(item) for item in raw.split(",")]
    if expected_points is not None and len(result) != expected_points:
        raise ResponseParseError("unexpected measurement point count", raw=raw)
    return result

