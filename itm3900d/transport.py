"""Transport helpers around PyVISA sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .exceptions import VisaConnectionError


@dataclass
class DryRunSession:
    """A tiny VISA-like session used by dry_run=True."""

    resource_name: str = "DRYRUN"
    timeout: int = 5000
    read_termination: str = "\n"
    write_termination: str = "\n"
    writes: list[str] = field(default_factory=list)
    query_responses: dict[str, str] = field(default_factory=dict)

    def write(self, command: str) -> None:
        self.writes.append(command)

    def query(self, command: str) -> str:
        self.writes.append(command)
        key = command.strip()
        if key in self.query_responses:
            return self.query_responses[key]
        upper = key.upper()
        if upper == "*IDN?":
            return "ITECH,IT-M3900D,DRYRUN,0\n"
        if upper == "SYST:ERR?" or upper == "SYSTEM:ERROR?":
            return '+0,"No error"\n'
        if upper.endswith("?"):
            return "0\n"
        return "\n"

    def read_raw(self) -> bytes:
        return b""

    def query_binary_values(self, *args: Any, **kwargs: Any) -> list[float]:
        self.writes.append(str(args[0]) if args else "")
        return []

    def clear(self) -> None:
        self.writes.append("<CLEAR>")

    def close(self) -> None:  # pragma: no cover - intentionally empty
        return None


@dataclass(frozen=True)
class ResourceStrings:
    vxi11: str
    socket: str


def ethernet_resources(ip: str, port: int = 5025) -> ResourceStrings:
    if not ip:
        raise ValueError("ip is required")
    return ResourceStrings(
        vxi11=f"TCPIP0::{ip}::inst0::INSTR",
        socket=f"TCPIP0::{ip}::{int(port)}::SOCKET",
    )


def require_pyvisa() -> Any:
    try:
        import pyvisa  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        raise VisaConnectionError(
            "pyvisa is required for real hardware connections. Install with `pip install pyvisa` "
            "and a backend such as NI-VISA or pyvisa-py."
        ) from exc
    return pyvisa
