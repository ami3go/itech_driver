"""ITECH compatibility API backed by the shared SCPI core."""
from __future__ import annotations

import math
import struct
import time
from typing import Union

from scpi_driver_core import ScpiClient, ScpiSession
from scpi_driver_core.exceptions import (
    ConfigurationError, ScpiTimeoutError, TransportError, UnsupportedOperationError,
    ResponseParseError,
)
from scpi_driver_core.scpi.codec import ScpiTextCodec
from scpi_driver_core.scpi.errors import ScpiErrorQueue, ScpiExecutionPolicy
from scpi_driver_core.transport.base import Transport
from scpi_driver_core.transport.visa import VisaTransport

from .exceptions import CommandError, InstrumentNotFoundError, TimeoutError

Number = Union[int, float]
BoolLike = Union[bool, int]
_BINARY_TYPES = frozenset("bBhHiIlLqQfd")


class BaseInstrument:
    """Own one core session. Construction opens transport but sends no SCPI."""

    def __init__(
        self, resource_name: str, timeout: int = 5000, termination: str = "\n",
        interface_kwargs: dict | None = None, *,
        transport: Transport | None = None, visa_library: str = "",
        resource_manager=None, chunk_size: int = 20 * 1024,
    ):
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
            raise ConfigurationError("timeout must be finite positive milliseconds")
        if termination not in ("\n", "\r\n", "\r"):
            raise ConfigurationError("termination must be LF, CRLF or CR")
        terminator = termination.encode("ascii")
        # Core currently does not expose arbitrary VISA open_resource kwargs.
        if interface_kwargs:
            raise ConfigurationError(
                "interface_kwargs is no longer supported; use core transport injection "
                "or visa_library/resource_manager/chunk_size"
            )
        if transport is not None and (visa_library or resource_manager is not None or chunk_size != 20 * 1024):
            raise ConfigurationError("VISA options cannot be combined with an injected transport")
        seconds = timeout / 1000
        if transport is None:
            transport = VisaTransport(
                resource_name, timeout_s=seconds, visa_library=visa_library,
                resource_manager=resource_manager, chunk_size=chunk_size,
            )
        codec = ScpiTextCodec(command_terminator=terminator, response_terminator=terminator)
        self.session = ScpiSession(
            resource_name, ScpiClient(transport, codec=codec, timeout_s=seconds),
            communication_timeout_s=seconds,
        )
        self._p = self
        self.system = self.source = self.output = self.status = None
        self.trigger = self.arb = self.battery = self.initiate = None
        self.abort = self.io = self.ieee = None
        try:
            self.session.open()
        except ScpiTimeoutError as exc:
            raise TimeoutError(str(exc)) from exc
        except TransportError as exc:
            raise InstrumentNotFoundError(str(exc)) from exc

    @property
    def client(self) -> ScpiClient:
        return self.session.client

    def write_scpi(self, cmd: str) -> None:
        # An ambiguous write must never be replayed automatically.
        try:
            self.client.write(cmd)
        except ScpiTimeoutError as exc:
            raise TimeoutError(str(exc)) from exc
        except TransportError as exc:
            raise CommandError(str(exc)) from exc

    def query_scpi(self, cmd: str, delay: float = 0.0) -> str:
        if not math.isfinite(delay) or delay < 0:
            raise ConfigurationError("delay must be finite and nonnegative")
        if delay:
            time.sleep(delay)
        # Even queries may have side effects (e.g. event register reads).
        try:
            return self.client.query(cmd).strip()
        except ScpiTimeoutError as exc:
            raise TimeoutError(str(exc)) from exc
        except TransportError as exc:
            raise CommandError(str(exc)) from exc

    def query_binary(self, cmd: str, datatype: str = "f", container=list,
                     *, is_big_endian: bool = False, consume_terminator: bool = True):
        """Decode an IEEE-488.2 definite-length block; default is little endian."""
        if len(datatype) != 1 or datatype not in _BINARY_TYPES:
            raise ConfigurationError(f"unsupported binary datatype: {datatype!r}")
        fmt = (">" if is_big_endian else "<") + datatype
        try:
            payload = self.client.query_binary_block(cmd, consume_terminator=consume_terminator)
        except ScpiTimeoutError as exc:
            raise TimeoutError(str(exc)) from exc
        except TransportError as exc:
            raise CommandError(str(exc)) from exc
        if len(payload) % struct.calcsize(fmt):
            raise ResponseParseError("binary payload is not a whole number of values", raw=payload)
        return container([item[0] for item in struct.iter_unpack(fmt, payload)])

    def enable_scpi_error_checking(self) -> None:
        """Opt in to destructive error-queue checks after successful writes.

        Existing errors may predate the current operation. A queue error does
        not imply that the command was not executed; never retry automatically.
        """
        self.client.enable_error_checking(
            ScpiErrorQueue(self.client, maximum_entries=21),
            ScpiExecutionPolicy(check_error_queue_after_write=True),
        )

    def disable_scpi_error_checking(self) -> None:
        self.client.disable_error_checking()

    def drain_scpi_errors(self, *, max_entries: int = 21):
        """Explicitly consume FIFO errors, with a bound including the zero sentinel."""
        if type(max_entries) is not int or not 1 <= max_entries <= 21:
            raise ConfigurationError("max_entries must be an integer in 1..21")
        return ScpiErrorQueue(self.client, maximum_entries=max_entries).drain()

    def identify(self) -> str:
        return self.query_scpi("*IDN?")

    def close(self) -> None:
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        try:
            self.close()
        except Exception as cleanup:
            if exc is None:
                raise
            if hasattr(exc, "add_note"):
                exc.add_note(f"Session cleanup failed: {cleanup!r}")
            else:
                exc.cleanup_error = cleanup
        return False

    @property
    def visa(self):
        """Raw VISA access bypasses core locking, framing and health tracking."""
        raise UnsupportedOperationError("use session.transport or client, not raw VISA")
