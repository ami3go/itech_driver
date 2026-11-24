"""ITECH compatibility API backed by the shared SCPI core."""
from __future__ import annotations

import math
import struct
import time
from typing import Union

from scpi_driver_core import ScpiClient, ScpiSession
from scpi_driver_core.models import Identity
from scpi_driver_core.exceptions import (
    ConfigurationError, ScpiTimeoutError, TransportError, UnsupportedOperationError,
    ResponseParseError,
)
from scpi_driver_core.scpi.errors import ScpiErrorQueue, ScpiExecutionPolicy
from scpi_driver_core.transport.base import Transport
from .connection import ConnectionConfig
from .utils.validation import nonnegative_number

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
        command_termination: str | None = None, response_termination: str | None = None,
        connection: ConnectionConfig | None = None,
    ):
        if interface_kwargs:
            raise ConfigurationError("interface_kwargs is no longer supported; use ConnectionConfig or core transport injection")
        if termination not in ("\n", "\r\n", "\r"):
            raise ConfigurationError("termination must be LF, CRLF or CR")
        if connection is not None:
            if (not isinstance(connection, ConnectionConfig) or resource_name != connection.resource
                    or timeout != 5000 or termination != "\n" or transport is not None
                    or visa_library or resource_manager is not None or chunk_size != 20 * 1024
                    or command_termination is not None or response_termination is not None):
                raise ConfigurationError("connection config cannot be mixed with legacy overrides")
            config = connection
        else:
            config = ConnectionConfig(
                resource_name, timeout,
                termination if command_termination is None else command_termination,
                termination if response_termination is None else response_termination,
                visa_library=visa_library, resource_manager=resource_manager, chunk_size=chunk_size)
        self._bind_session(config.make_session(transport))
        try:
            self.session.open()
        except ScpiTimeoutError as exc:
            raise TimeoutError(str(exc)) from exc
        except TransportError as exc:
            raise InstrumentNotFoundError(str(exc)) from exc

    def _bind_session(self, session: ScpiSession) -> None:
        """Bind one existing core session; does not open or probe transport."""
        self.session = session
        self._p = self
        self.system = self.source = self.output = self.status = None
        self.trigger = self.arb = self.battery = self.initiate = None
        self.abort = self.io = self.ieee = None

    @property
    def client(self) -> ScpiClient:
        return self.session.client

    def _assert_write_authorized(self) -> None:
        """Policy hook for compound operations; base has no remote policy."""
        return None

    def write_scpi(self, cmd: str) -> None:
        # An ambiguous write must never be replayed automatically.
        try:
            self.client.write(cmd)
        except ScpiTimeoutError as exc:
            raise TimeoutError(str(exc)) from exc
        except TransportError as exc:
            raise CommandError(str(exc)) from exc

    def query_scpi(self, cmd: str, delay: float = 0.0) -> str:
        """Legacy pre-query delay shares a bounded transaction budget.

        The budget begins after acquisition of the operation lock. It does not
        preempt other operations already holding that lock. No OPC is implied.
        """
        nonnegative_number(delay, "delay")
        with self.session.operation_lock():
            try:
                if not delay:
                    return self.client.query(cmd).strip()
                budget = self.client.timeout_s
                if budget is None or delay >= budget:
                    raise ConfigurationError("delay must be shorter than the finite communication timeout")
                deadline = time.monotonic() + budget
                time.sleep(delay)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("query deadline exhausted before transmission")
                return self.client.query(cmd, timeout_s=remaining).strip()
            except ScpiTimeoutError as exc:
                # A locally exhausted budget is already the public timeout type.
                if isinstance(exc, TimeoutError):
                    raise
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

    def identity_snapshot(self, *, refresh: bool = False) -> Identity:
        """Immutable generation-scoped metadata via the shared core."""
        try:
            return self.session.get_identity(refresh=refresh)
        except ScpiTimeoutError as exc:
            raise TimeoutError(str(exc)) from exc
        except TransportError as exc:
            raise CommandError(str(exc)) from exc

    def identify(self) -> str:
        return self.query_scpi("*IDN?")

    def close(self) -> None:
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        try:
            self.close()
        except BaseException as cleanup:
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
