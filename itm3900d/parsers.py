"""SCPI formatting and parsing utilities."""

from __future__ import annotations

import csv
import io
import re
from typing import Literal

from .types import InstrumentErrorRecord

_TRUE = {"1", "ON", "TRUE", "T", "YES", "Y"}
_FALSE = {"0", "OFF", "FALSE", "F", "NO", "N"}
_NUMERIC_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


def to_bool(value: bool | int | str) -> Literal["ON", "OFF"]:
    """Convert Python/user boolean forms to SCPI ON/OFF."""
    if isinstance(value, bool):
        return "ON" if value else "OFF"
    if isinstance(value, int):
        if value == 1:
            return "ON"
        if value == 0:
            return "OFF"
    text = str(value).strip().upper()
    if text in _TRUE:
        return "ON"
    if text in _FALSE:
        return "OFF"
    raise ValueError(f"Invalid boolean value: {value!r}")


def from_bool_response(value: str) -> bool:
    """Parse a SCPI boolean query response."""
    text = str(value).strip().upper()
    if text in _TRUE:
        return True
    if text in _FALSE:
        return False
    raise ValueError(f"Invalid boolean response: {value!r}")


def format_float(value: float | int | str) -> str:
    """Format a numeric or SCPI selector/suffixed value without losing user intent."""
    if isinstance(value, bool):
        raise TypeError("Boolean is not a numeric SCPI value")
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return format(value, ".12g")
    text = str(value).strip()
    if not text:
        raise ValueError("Empty numeric value")
    return text


def parse_float(value: str) -> float:
    return float(str(value).strip())


def parse_csv_floats(value: str) -> list[float]:
    text = str(value).strip()
    if not text:
        return []
    return [float(item.strip()) for item in text.split(",") if item.strip()]


def parse_csv_mixed(value: str) -> list[str | float]:
    text = str(value).strip()
    if not text:
        return []
    reader = csv.reader(io.StringIO(text))
    row = next(reader, [])
    out: list[str | float] = []
    for item in row:
        item = item.strip()
        if _NUMERIC_RE.match(item):
            out.append(float(item))
        else:
            out.append(item)
    return out


def parse_status_register(value: str) -> int:
    return int(str(value).strip(), 0)


def parse_scpi_error(value: str) -> InstrumentErrorRecord:
    """Parse responses like '+0,"No error"' or '-113,"Undefined header"'."""
    raw = str(value).strip()
    match = re.match(r"^\s*([+-]?\d+)\s*,\s*(.*)\s*$", raw)
    if not match:
        return InstrumentErrorRecord(code=0, message=raw, raw=raw) if "NO ERROR" in raw.upper() else InstrumentErrorRecord(code=-9999, message=raw, raw=raw)
    code = int(match.group(1))
    message = match.group(2).strip().strip('"')
    return InstrumentErrorRecord(code=code, message=message, raw=raw)


def parse_definite_length_block(data: bytes) -> bytes:
    """Parse IEEE 488.2 definite-length block data: #<n><len><payload>."""
    if not data:
        return b""
    if not data.startswith(b"#"):
        raise ValueError("Block does not start with '#'")
    if len(data) < 2:
        raise ValueError("Incomplete block header")
    n_digits_byte = data[1:2]
    if not n_digits_byte.isdigit():
        raise ValueError("Invalid block length digit count")
    n_digits = int(n_digits_byte)
    if n_digits == 0:
        # Indefinite-length block: return the rest and let caller define termination.
        return data[2:]
    header_end = 2 + n_digits
    if len(data) < header_end:
        raise ValueError("Incomplete block length field")
    length_text = data[2:header_end]
    if not length_text.isdigit():
        raise ValueError("Invalid block length field")
    payload_len = int(length_text)
    payload_end = header_end + payload_len
    if len(data) < payload_end:
        raise ValueError(f"Incomplete block payload: expected {payload_len}, got {len(data) - header_end}")
    return data[header_end:payload_end]


def maybe_parse_ascii_or_block(data: bytes | str) -> bytes | list[float]:
    """Return block payload bytes for binary blocks, otherwise parse CSV floats."""
    raw = data.encode() if isinstance(data, str) else data
    stripped = raw.strip()
    if stripped.startswith(b"#"):
        return parse_definite_length_block(stripped)
    return parse_csv_floats(stripped.decode(errors="replace"))
