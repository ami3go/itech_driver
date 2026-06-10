"""Status register bit helpers.

The exact bit meaning can depend on firmware/options. These helpers keep raw
integer status values available and provide simple bit decoding.
"""

from __future__ import annotations


def bit_is_set(register_value: int, bit: int) -> bool:
    if bit < 0:
        raise ValueError("bit must be >= 0")
    return bool(int(register_value) & (1 << bit))


def set_bits(register_value: int) -> list[int]:
    value = int(register_value)
    return [bit for bit in range(value.bit_length()) if bit_is_set(value, bit)]
