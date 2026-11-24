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



def binary_array_query(parent, header: str, *, datatype: str, byte_order: str,
                       expected_points: int, binary_confirmed: bool,
                       consume_terminator: bool) -> list[float]:
    """Decode an explicitly confirmed IEEE-488.2 float block, not a format guess."""
    import math
    if binary_confirmed is not True:
        raise ConfigurationError("confirm device binary block format and encoding first")
    if datatype not in ("f", "d") or byte_order not in ("little", "big"):
        raise ConfigurationError("explicit float32/64 datatype and little/big byte order required")
    if type(expected_points) is not int or expected_points <= 0:
        raise ConfigurationError("positive expected_points required")
    if type(consume_terminator) is not bool:
        raise ConfigurationError("explicit boolean terminator policy required")
    result = parent.query_binary(header, datatype=datatype,
                                 is_big_endian=byte_order == "big",
                                 consume_terminator=consume_terminator)
    if len(result) != expected_points or any(not math.isfinite(x) for x in result):
        raise ResponseParseError("invalid binary sample count or nonfinite value", raw=repr(result[:8]))
    return result
