"""Public dataclasses and type helpers for IT-M3900D."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal


@dataclass(frozen=True)
class InstrumentErrorRecord:
    """One parsed entry from the instrument SCPI error queue."""

    code: int
    message: str
    raw: str

    @property
    def is_no_error(self) -> bool:
        return self.code == 0


@dataclass(frozen=True)
class ScpiLogRecord:
    """Single low-level SCPI transaction log record."""

    timestamp: float
    resource: str | None
    direction: Literal["write", "query", "read_raw", "query_raw", "error"]
    command: str | None = None
    response: str | bytes | None = None
    elapsed_s: float | None = None
    exception: BaseException | None = None


ScpiLogger = Callable[[ScpiLogRecord], None]


@dataclass(frozen=True)
class ScpiParameter:
    name: str
    kind: str = "str"
    optional: bool = False


@dataclass(frozen=True)
class ScpiReturn:
    kind: str = "str"
    description: str = ""


@dataclass(frozen=True)
class ScpiCommand:
    key: str
    scpi: str
    subsystem: str
    operation: Literal["set", "query", "action"]
    parameters: tuple[ScpiParameter, ...] = ()
    returns: ScpiReturn | None = None
    supports_min_max_def: bool = False
    valid_values: tuple[str, ...] = ()
    default: str | float | int | None = None
    page: int | None = None
    source: Literal["toc", "syntax", "query_syntax", "manual_verified", "hardware_verified"] = "toc"
    verification: Literal["not_tested", "mock_tested", "hardware_tested"] = "not_tested"
    safety_class: Literal["safe", "guarded", "dangerous"] = "safe"
    requires_confirmation: bool = False
    requires_output_enable_permission: bool = False
