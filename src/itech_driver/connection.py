"""Typed connection construction; the core owns byte transport and session I/O."""
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlsplit

from scpi_driver_core import ConfigurationError, ScpiClient, ScpiSession
from scpi_driver_core.scpi.codec import ScpiTextCodec
from scpi_driver_core.transport import TcpTransport, SerialTransport, VisaTransport
from scpi_driver_core.transport.base import Transport
from .utils.validation import finite_number, exact_integer

DEFAULT_TCP_PORT = 30000
DEFAULT_CHUNK_SIZE = 20 * 1024
_ENDINGS = ("\n", "\r\n", "\r")


@dataclass(frozen=True)
class ConnectionConfig:
    resource: str
    timeout_ms: float = 5000
    command_termination: str = "\n"
    response_termination: str = "\n"
    interface: Literal["auto", "visa", "tcp", "vcp"] = "auto"
    visa_library: str = ""
    resource_manager: object | None = None
    chunk_size: int = DEFAULT_CHUNK_SIZE
    baudrate: int = 9600
    bytesize: int = 8
    parity: str = "N"
    stopbits: float = 1
    dtr: bool | None = None
    rts: bool | None = None

    def __post_init__(self):
        if not isinstance(self.resource, str) or not self.resource.strip():
            raise ConfigurationError("resource is required")
        if finite_number(self.timeout_ms, "timeout") <= 0:
            raise ConfigurationError("timeout must be positive milliseconds")
        if self.command_termination not in _ENDINGS or self.response_termination not in _ENDINGS:
            raise ConfigurationError("terminations must be LF, CRLF or CR")
        if self.interface not in ("auto", "visa", "tcp", "vcp"):
            raise ConfigurationError("unknown interface")
        if not isinstance(self.visa_library, str):
            raise ConfigurationError("visa_library must be str")
        if type(self.chunk_size) is not int or self.chunk_size <= 0:
            raise ConfigurationError("chunk_size must be a positive integer")
        if type(self.baudrate) is not int or self.baudrate <= 0:
            raise ConfigurationError("baudrate must be a positive integer")
        if type(self.bytesize) is not int or self.bytesize not in (5, 6, 7, 8):
            raise ConfigurationError("bytesize must be 5, 6, 7 or 8")
        if not isinstance(self.parity, str) or self.parity.upper() not in ("N", "E", "O"):
            raise ConfigurationError("parity must be N, E or O")
        if type(self.stopbits) not in (int, float) or self.stopbits not in (1, 2):
            raise ConfigurationError("stopbits must be 1 or 2")
        if any(x is not None and type(x) is not bool for x in (self.dtr, self.rts)):
            raise ConfigurationError("dtr/rts must be bool or None")

    @property
    def kind(self):
        if self.interface != "auto":
            return self.interface
        if self.resource.startswith("tcp://"):
            return "tcp"
        if self.resource.startswith("vcp:"):
            return "vcp"
        return "visa"

    @property
    def timeout_s(self):
        return self.timeout_ms / 1000

    def make_session(self, transport: Transport | None = None) -> ScpiSession:
        """Build but do not open a single session."""
        visa_options = bool(self.visa_library or self.resource_manager is not None
                            or self.chunk_size != DEFAULT_CHUNK_SIZE)
        serial_options = (self.baudrate, self.bytesize, self.parity, self.stopbits,
                          self.dtr, self.rts) != (9600, 8, "N", 1, None, None)
        if transport is not None:
            if self.interface != "auto" or visa_options or serial_options:
                raise ConfigurationError("connection options conflict with injected transport")
        else:
            kind = self.kind
            if kind != "visa" and visa_options:
                raise ConfigurationError("VISA options require VISA interface")
            if kind != "vcp" and serial_options:
                raise ConfigurationError("serial options require VCP interface")
            if kind == "tcp":
                try:
                    uri = urlsplit(self.resource)
                    if (uri.scheme != "tcp" or not uri.hostname or uri.username is not None
                            or uri.password is not None or uri.path or uri.query or uri.fragment):
                        raise ValueError("expected tcp://host:port")
                    host, port = uri.hostname, uri.port
                except ValueError as exc:
                    raise ConfigurationError("invalid TCP resource") from exc
                if port is None:
                    port = DEFAULT_TCP_PORT
                exact_integer(port, minimum=1, maximum=65535, name="port")
                transport = TcpTransport(host, port, timeout_s=self.timeout_s,
                                         connect_timeout_s=self.timeout_s)
            elif kind == "vcp":
                if not self.resource.startswith("vcp:") or not self.resource[4:].strip():
                    raise ConfigurationError("expected vcp:PORT")
                transport = SerialTransport(
                    self.resource[4:], baudrate=self.baudrate, bytesize=self.bytesize,
                    parity=self.parity, stopbits=self.stopbits, dtr=self.dtr, rts=self.rts,
                    timeout_s=self.timeout_s, write_timeout_s=self.timeout_s)
            else:
                transport = VisaTransport(self.resource, timeout_s=self.timeout_s,
                    visa_library=self.visa_library, resource_manager=self.resource_manager,
                    chunk_size=self.chunk_size)
        codec = ScpiTextCodec(command_terminator=self.command_termination.encode("ascii"),
                             response_terminator=self.response_termination.encode("ascii"))
        return ScpiSession(self.resource, ScpiClient(transport, codec=codec, timeout_s=self.timeout_s),
                           communication_timeout_s=self.timeout_s)
