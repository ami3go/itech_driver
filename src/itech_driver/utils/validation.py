"""Typed argument validation; no invented instrument limits."""
from __future__ import annotations

import math
from ..exceptions import ValidationError

Number = int | float


def finite_number(value: Number, name: str = "value") -> Number:
    try:
        valid = type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise ValidationError(f"{name} must be a finite real number")
    return value


def nonnegative_number(value: Number, name: str = "value") -> Number:
    finite_number(value, name)
    if value < 0:
        raise ValidationError(f"{name} must be nonnegative")
    return value


def exact_integer(value: int, *, minimum: int, maximum: int, name: str = "value") -> int:
    if (type(minimum) is not int or type(maximum) is not int or minimum > maximum
            or type(value) is not int or not minimum <= value <= maximum):
        raise ValidationError(f"{name} must be an integer within {minimum!r}..{maximum!r}")
    return value


def validate_bounds(minimum: Number, maximum: Number) -> None:
    finite_number(minimum, "minimum")
    finite_number(maximum, "maximum")
    if minimum > maximum:
        raise ValidationError("minimum exceeds maximum")


def validate_range(value: Number, range_tuple: tuple[Number, Number], value_name: str) -> Number:
    if not isinstance(range_tuple, (tuple, list)) or len(range_tuple) != 2:
        raise ValidationError(f"{value_name} requires explicit ordered bounds")
    minimum, maximum = range_tuple
    validate_bounds(minimum, maximum)
    finite_number(value, value_name)
    if not minimum <= value <= maximum:
        raise ValidationError(f"{value_name} outside permitted range {minimum}..{maximum}: {value!r}")
    return value


def validate_voltage(value: Number, min_val: Number | None = None,
                     max_val: Number | None = None) -> Number:
    """Require explicit bounds (previous arbitrary defaults removed)."""
    return validate_range(value, (min_val, max_val), "voltage")


def validate_current(value: Number, min_val: Number | None = None,
                     max_val: Number | None = None) -> Number:
    """Require explicit bounds (previous arbitrary defaults removed)."""
    return validate_range(value, (min_val, max_val), "current")


def validate_channel(channel: int, max_channels: int | None = None) -> int:
    """Require explicit model channel count; reject bool and fractional values."""
    if type(max_channels) is not int or max_channels < 1:
        raise ValidationError("explicit positive model channel count required")
    return exact_integer(channel, minimum=1, maximum=max_channels, name="channel")


def strict_bool(value: bool | int, name: str = "state") -> bool:
    if type(value) not in (bool, int) or value not in (0, 1):
        raise ValidationError(f"{name} must be bool or 0/1")
    return bool(value)
