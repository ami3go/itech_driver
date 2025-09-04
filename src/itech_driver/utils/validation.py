"""Input validation utilities."""

from typing import Union, Tuple
from ..exceptions import ValidationError

Number = Union[int, float]

def validate_voltage(value: Number, min_val: Number = 0, max_val: Number = 60) -> Number:
    """Validate voltage value."""
    if not min_val <= value <= max_val:
        raise ValidationError(f"Voltage {value}V is outside valid range [{min_val}, {max_val}]V")
    return value

def validate_current(value: Number, min_val: Number = 0, max_val: Number = 10) -> Number:
    """Validate current value."""
    if not min_val <= value <= max_val:
        raise ValidationError(f"Current {value}A is outside valid range [{min_val}, {max_val}]A")
    return value

def validate_range(value: Number, range_tuple: Tuple[Number, Number], value_name: str) -> Number:
    """Generic range validation."""
    min_val, max_val = range_tuple
    if not min_val <= value <= max_val:
        raise ValidationError(f"{value_name} {value} is outside valid range [{min_val}, {max_val}]")
    return value

def validate_channel(channel: int, max_channels: int = 2) -> int:
    """Validate channel number."""
    if not 1 <= channel <= max_channels:
        raise ValidationError(f"Channel {channel} is invalid. Must be between 1 and {max_channels}")
    return channel