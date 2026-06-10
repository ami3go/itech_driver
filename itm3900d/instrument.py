"""Production-intent PyVISA driver for ITECH IT-M3900D supplies."""

from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Literal, cast

from .command_catalog import COMMANDS, COMMANDS_BY_KEY, ScpiCommand, command_header
from .exceptions import (
    InstrumentCommandError,
    InstrumentError,
    InstrumentTimeoutError,
    ITM3900DError,
    OutputEnableConfirmationRequired,
    OutputEnableNotAllowedError,
    OutputNotSafeError,
    SafetyLimitError,
    UnsupportedCommandError,
    VisaConnectionError,
)
from .parsers import (
    format_float,
    from_bool_response,
    maybe_parse_ascii_or_block,
    parse_csv_floats,
    parse_csv_mixed,
    parse_float,
    parse_scpi_error,
    parse_status_register,
    to_bool,
)
from .safety import SafetyPolicy
from .transport import DryRunSession, ethernet_resources, require_pyvisa
from .types import InstrumentErrorRecord, ScpiLogRecord, ScpiLogger


@dataclass
class ArbStep:
    """Single ARB/list step."""

    level: float
    dwell_s: float
    slew: float | None = None
    trigout: str | None = None


class _ScpiProxy:
    """Dynamic access to the machine-readable SCPI catalog.

    Example:
        psu.scpi.source_voltage_level_immediate_amplitude(12.0)
        psu.scpi.source_voltage_level_immediate_amplitude_query()
    """

    def __init__(self, instrument: "ITM3900D") -> None:
        self._instrument = instrument

    def __getattr__(self, key: str) -> Callable[..., Any]:
        if key not in COMMANDS_BY_KEY:
            source_key = f"source_{key}"
            if source_key in COMMANDS_BY_KEY:
                key = source_key
            else:
                raise AttributeError(key)

        def call(*args: Any, confirm: bool = False, cast: Callable[[str], Any] | type | None = None) -> Any:
            return self._instrument.invoke(key, *args, confirm=confirm, cast=cast)

        call.__name__ = key
        call.__doc__ = f"Dynamic wrapper for {COMMANDS_BY_KEY[key].scpi}"
        return call


class ITM3900D:
    """Safe-by-default IT-M3900D PyVISA driver.

    The constructor does not energize output. Use :meth:`output_on` with
    ``confirm=True`` and a suitable :class:`SafetyPolicy` when you intentionally
    want to enable the output.
    """

    def __init__(
        self,
        resource: str | None = None,
        *,
        ip: str | None = None,
        port: int = 5025,
        lan_mode: Literal["auto", "vxi11", "socket"] = "auto",
        backend: str | None = None,
        timeout_ms: int = 5000,
        query_delay_s: float = 0.0,
        read_termination: str = "\n",
        write_termination: str = "\n",
        auto_remote: bool = True,
        lock_front_panel: bool = False,
        safe_startup: bool = True,
        validate_idn: bool = True,
        idn_regex: str | None = None,
        strict: bool = True,
        dry_run: bool = False,
        safety: SafetyPolicy | None = None,
        allow_output_enable: bool = False,
        scpi_logger: ScpiLogger | None = None,
        return_local_on_close: bool = False,
        session: Any | None = None,
    ) -> None:
        self.resource = resource
        self.ip = ip
        self.port = int(port)
        self.lan_mode = lan_mode
        self.backend = backend
        self.timeout_ms = int(timeout_ms)
        self.query_delay_s = float(query_delay_s)
        self.read_termination = read_termination
        self.write_termination = write_termination
        self.auto_remote = bool(auto_remote)
        self.lock_front_panel = bool(lock_front_panel)
        self.safe_startup = bool(safe_startup)
        self.validate_idn = bool(validate_idn)
        self.idn_regex = idn_regex
        self.strict = bool(strict)
        self.dry_run = bool(dry_run)
        self.safety = safety or SafetyPolicy()
        self.allow_output_enable = bool(allow_output_enable)
        self.return_local_on_close = bool(return_local_on_close)
        self.scpi_logger = scpi_logger
        self._lock = threading.RLock()
        self._rm: Any | None = None
        self._session: Any | None = session
        self._is_open = session is not None
        self._opened_resource: str | None = resource
        self._voltage_setpoint: float | None = None
        self._current_setpoint: float | None = None
        self._power_limit: float | None = None
        self._last_output_on_time: float | None = None
        self.scpi = _ScpiProxy(self)

    # ------------------------------------------------------------------
    # Class helpers / resource discovery
    # ------------------------------------------------------------------
    @classmethod
    def list_resources(cls, backend: str | None = None) -> list[str]:
        pyvisa = require_pyvisa()
        rm = pyvisa.ResourceManager(backend) if backend else pyvisa.ResourceManager()
        return list(rm.list_resources())

    @classmethod
    def find_usb(cls, idn_regex: str | None = None, backend: str | None = None, timeout_ms: int = 1000) -> list[str]:
        """Find USB-TMC resources whose *IDN? looks like ITECH IT-M3900D/IT39."""
        pyvisa = require_pyvisa()
        rm = pyvisa.ResourceManager(backend) if backend else pyvisa.ResourceManager()
        candidates = [r for r in rm.list_resources() if str(r).upper().startswith("USB") and str(r).upper().endswith("INSTR")]
        pattern = re.compile(idn_regex or r"(ITECH|IT-M3900D|IT39)", re.IGNORECASE)
        matches: list[str] = []
        for res in candidates:
            session = None
            try:
                session = rm.open_resource(res)
                session.timeout = timeout_ms
                session.read_termination = "\n"
                session.write_termination = "\n"
                idn = str(session.query("*IDN?"))
                if pattern.search(idn):
                    matches.append(str(res))
            except Exception:
                continue
            finally:
                try:
                    if session is not None:
                        session.close()
                except Exception:
                    pass
        return matches

    @classmethod
    def open_usb(cls, resource: str | None = None, **kwargs: Any) -> "ITM3900D":
        if resource is None and not kwargs.get("dry_run", False):
            found = cls.find_usb(idn_regex=kwargs.get("idn_regex"), backend=kwargs.get("backend"))
            if not found:
                raise VisaConnectionError("No compatible USB-TMC IT-M3900D/IT39 resource found")
            resource = found[0]
        inst = cls(resource=resource or "DRYRUN::USB::INSTR", **kwargs)
        inst.open()
        return inst

    @classmethod
    def open_ethernet(
        cls,
        ip: str,
        port: int = 5025,
        lan_mode: Literal["auto", "vxi11", "socket"] = "auto",
        **kwargs: Any,
    ) -> "ITM3900D":
        inst = cls(ip=ip, port=port, lan_mode=lan_mode, **kwargs)
        inst.open()
        return inst

    @staticmethod
    def ethernet_resource_strings(ip: str, port: int = 5025) -> tuple[str, str]:
        resources = ethernet_resources(ip, port)
        return resources.vxi11, resources.socket

    # ------------------------------------------------------------------
    # Context manager / session lifecycle
    # ------------------------------------------------------------------
    def __enter__(self) -> "ITM3900D":
        if not self.is_open:
            self.open()
        return self

    def __exit__(self, exc_type: Any, exc: BaseException | None, tb: Any) -> None:
        if exc is not None and self.safety.output_off_on_exception:
            try:
                self.output_off(verify=False)
            except Exception:
                pass
        self.close()

    @property
    def is_open(self) -> bool:
        return bool(self._is_open and self._session is not None)

    @property
    def session(self) -> Any:
        if self._session is None:
            raise VisaConnectionError("Instrument session is not open")
        return self._session

    @property
    def dry_run_writes(self) -> list[str]:
        if isinstance(self._session, DryRunSession):
            return self._session.writes
        return []

    def open(self) -> None:
        """Open the VISA session. Does not enable output."""
        with self._lock:
            if self.is_open:
                return
            if self.dry_run:
                self._session = DryRunSession(resource_name=self.resource or (f"DRYRUN::TCPIP::{self.ip}" if self.ip else "DRYRUN::INSTR"))
                self._is_open = True
                self._opened_resource = self._session.resource_name
            else:
                pyvisa = require_pyvisa()
                self._rm = pyvisa.ResourceManager(self.backend) if self.backend else pyvisa.ResourceManager()
                last_exc: Exception | None = None
                for resource in self._make_resource_candidates():
                    try:
                        session = self._rm.open_resource(resource)
                        session.timeout = self.timeout_ms
                        if hasattr(session, "read_termination"):
                            session.read_termination = self.read_termination
                        if hasattr(session, "write_termination"):
                            session.write_termination = self.write_termination
                        self._session = session
                        self._opened_resource = resource
                        self._is_open = True
                        break
                    except Exception as exc:  # pragma: no cover - hardware/backend dependent
                        last_exc = exc
                if not self.is_open:
                    raise VisaConnectionError(f"Could not open IT-M3900D VISA resource: {last_exc}") from last_exc

            if self.validate_idn:
                idn = self.idn()
                pattern = re.compile(self.idn_regex or r"(ITECH|IT-M3900D|IT39)", re.IGNORECASE)
                if not pattern.search(idn):
                    self.close()
                    raise VisaConnectionError(f"Unexpected *IDN? response: {idn!r}")
            if self.auto_remote:
                self.set_remote()
            if self.lock_front_panel:
                self.set_remote_with_lock()

    def close(self) -> None:
        with self._lock:
            if not self.is_open:
                return
            if self.safety.output_off_on_close:
                try:
                    self.output_off(verify=self.safety.verify_output_off)
                except Exception:
                    # Closing should continue; user can inspect logs/errors.
                    pass
            if self.return_local_on_close:
                try:
                    self.set_local()
                except Exception:
                    pass
            try:
                self.session.close()
            finally:
                self._session = None
                self._is_open = False

    def _make_resource_candidates(self) -> list[str]:
        if self.resource:
            return [self.resource]
        if self.ip:
            resources = ethernet_resources(self.ip, self.port)
            if self.lan_mode == "vxi11":
                return [resources.vxi11]
            if self.lan_mode == "socket":
                return [resources.socket]
            return [resources.vxi11, resources.socket]
        raise VisaConnectionError("resource or ip must be provided")

    # ------------------------------------------------------------------
    # Low-level SCPI I/O
    # ------------------------------------------------------------------
    def _log(self, direction: Literal["write", "query", "read_raw", "query_raw", "error"], command: str | None = None,
             response: str | bytes | None = None, elapsed_s: float | None = None,
             exception: BaseException | None = None) -> None:
        if self.scpi_logger is None:
            return
        self.scpi_logger(
            ScpiLogRecord(
                timestamp=time.time(),
                resource=self._opened_resource or self.resource,
                direction=direction,
                command=command,
                response=response,
                elapsed_s=elapsed_s,
                exception=exception,
            )
        )

    def write(self, command: str, *, check_errors: bool | None = None, confirm: bool = False) -> None:
        """Write a raw SCPI command.

        Raw output-enable commands are guarded. Prefer high-level wrappers.
        """
        if check_errors is None:
            check_errors = self.strict
        self._guard_raw_command(command, confirm=confirm)
        self._write_no_check(command)
        if check_errors:
            self.raise_on_error()

    def _write_no_check(self, command: str) -> None:
        with self._lock:
            command = command.strip()
            start = time.perf_counter()
            try:
                self.session.write(command)
                self._log("write", command=command, elapsed_s=time.perf_counter() - start)
            except Exception as exc:
                self._log("error", command=command, elapsed_s=time.perf_counter() - start, exception=exc)
                self._raise_transport_exception(exc)

    def query(self, command: str, *, cast: Callable[[str], Any] | type = str) -> Any:
        with self._lock:
            command = command.strip()
            start = time.perf_counter()
            try:
                if self.query_delay_s > 0:
                    time.sleep(self.query_delay_s)
                response = str(self.session.query(command)).strip()
                self._log("query", command=command, response=response, elapsed_s=time.perf_counter() - start)
                return self._cast_response(response, cast)
            except Exception as exc:
                self._log("error", command=command, elapsed_s=time.perf_counter() - start, exception=exc)
                self._raise_transport_exception(exc)

    def read_raw(self) -> bytes:
        with self._lock:
            start = time.perf_counter()
            try:
                data = bytes(self.session.read_raw())
                self._log("read_raw", response=data, elapsed_s=time.perf_counter() - start)
                return data
            except Exception as exc:
                self._log("error", elapsed_s=time.perf_counter() - start, exception=exc)
                self._raise_transport_exception(exc)

    def query_raw(self, command: str) -> bytes:
        with self._lock:
            self._write_no_check(command)
            return self.read_raw()

    def clear(self) -> None:
        with self._lock:
            try:
                self.session.clear()
            except Exception as exc:
                self._raise_transport_exception(exc)

    def wait_opc(self, timeout_ms: int | None = None) -> bool:
        old_timeout = getattr(self.session, "timeout", None)
        try:
            if timeout_ms is not None and hasattr(self.session, "timeout"):
                self.session.timeout = int(timeout_ms)
            return bool(int(str(self.query("*OPC?", cast=str)).strip()))
        finally:
            if timeout_ms is not None and old_timeout is not None and hasattr(self.session, "timeout"):
                self.session.timeout = old_timeout

    def check_errors(self, max_reads: int = 25) -> list[InstrumentErrorRecord]:
        records: list[InstrumentErrorRecord] = []
        for _ in range(max_reads):
            raw = str(self.query("SYST:ERR?", cast=str))
            record = parse_scpi_error(raw)
            records.append(record)
            if record.is_no_error:
                break
        return records

    def raise_on_error(self) -> None:
        errors = [e for e in self.check_errors() if not e.is_no_error]
        if not errors:
            return
        first = errors[0]
        msg = "; ".join(f"{e.code}: {e.message}" for e in errors)
        if first.code == -410 or "QUERY" in first.message.upper():
            raise InstrumentCommandError(f"SCPI query/command error(s): {msg}")
        raise InstrumentError(f"Instrument error queue contains error(s): {msg}")

    def invoke(self, key: str, *args: Any, confirm: bool = False, cast: Callable[[str], Any] | type | None = None) -> Any:
        """Invoke any command from command_catalog.py by key."""
        if key not in COMMANDS_BY_KEY:
            raise UnsupportedCommandError(f"Unknown SCPI catalog key: {key}")
        cmd = COMMANDS_BY_KEY[key]
        self._guard_catalog_command(cmd, args, confirm=confirm)
        header = command_header(cmd)
        suffix = ""
        if args:
            suffix = " " + ",".join(self._format_arg(a) for a in args)
        scpi = f"{header}{suffix}"
        if cmd.operation == "query":
            return self.query(scpi, cast=cast or str)
        self.write(scpi, confirm=confirm)
        return None

    def scpi_keys(self, text: str | None = None) -> list[str]:
        if text is None:
            return sorted(COMMANDS_BY_KEY)
        t = text.lower()
        return sorted(k for k, cmd in COMMANDS_BY_KEY.items() if t in k.lower() or t in cmd.scpi.lower())

    @staticmethod
    def _format_arg(value: Any) -> str:
        if isinstance(value, bool):
            return to_bool(value)
        return str(value)

    @staticmethod
    def _cast_response(response: str, cast_to: Callable[[str], Any] | type) -> Any:
        if cast_to is str:
            return response
        if cast_to is bool:
            return from_bool_response(response)
        if cast_to is int:
            return int(response.strip())
        if cast_to is float:
            return float(response.strip())
        if cast_to is list:
            return parse_csv_mixed(response)
        return cast_to(response)

    def _raise_transport_exception(self, exc: Exception) -> None:
        msg = str(exc)
        if "timeout" in msg.lower() or "VI_ERROR_TMO" in msg:
            raise InstrumentTimeoutError(msg) from exc
        raise VisaConnectionError(msg) from exc

    def _guard_raw_command(self, command: str, *, confirm: bool = False) -> None:
        normalized = re.sub(r"\s+", " ", command.strip().upper())
        if re.match(r"^:?OUTP(?:UT)?(?::STAT(?:E)?)?\s+(1|ON)\b", normalized):
            self._require_output_enable_allowed(confirm=confirm)
        if re.match(r"^:?OUTP(?:UT)?:PON:STAT(?:E)?\s+LAST_ON\b", normalized):
            self._require_output_enable_allowed(confirm=confirm)

    def _guard_catalog_command(self, cmd: ScpiCommand, args: tuple[Any, ...], *, confirm: bool = False) -> None:
        if cmd.safety_class == "safe":
            return
        upper_args = [str(a).strip().upper() for a in args]
        is_output_off = command_header(cmd).upper().replace("[", "").startswith("OUTPUT") and upper_args and upper_args[0] in {"0", "OFF", "FALSE"}
        if is_output_off:
            return
        if cmd.safety_class == "dangerous":
            self._require_output_enable_allowed(confirm=confirm)
        elif cmd.requires_confirmation and not confirm:
            raise OutputEnableConfirmationRequired(f"Command {cmd.scpi} requires confirm=True")

    # ------------------------------------------------------------------
    # Safety helpers
    # ------------------------------------------------------------------
    def _numeric_or_none(self, value: float | int | str) -> float | None:
        if isinstance(value, (float, int)) and not isinstance(value, bool):
            return float(value)
        text = str(value).strip().upper()
        if text in {"MIN", "MINIMUM", "DEF", "DEFAULT"}:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    def _require_verifiable_numeric(self, name: str, value: float | int | str) -> float | None:
        numeric = self._numeric_or_none(value)
        text = str(value).strip().upper()
        if numeric is None and text in {"MAX", "MAXIMUM"}:
            raise SafetyLimitError(f"{name}=MAX is not allowed because it cannot be checked against SafetyPolicy")
        return numeric

    def _check_voltage_limit(self, value: float | int | str) -> float | None:
        numeric = self._require_verifiable_numeric("voltage", value)
        if numeric is not None and self.safety.max_voltage_v is not None and abs(numeric) > self.safety.max_voltage_v:
            raise SafetyLimitError(f"Voltage {numeric} V exceeds policy max {self.safety.max_voltage_v} V")
        return numeric

    def _check_current_limit(self, value: float | int | str) -> float | None:
        numeric = self._require_verifiable_numeric("current", value)
        if numeric is not None and self.safety.max_current_a is not None and abs(numeric) > self.safety.max_current_a:
            raise SafetyLimitError(f"Current {numeric} A exceeds policy max {self.safety.max_current_a} A")
        return numeric

    def _check_power_limit(self, value: float | int | str) -> float | None:
        numeric = self._require_verifiable_numeric("power", value)
        if numeric is not None and self.safety.max_power_w is not None and abs(numeric) > self.safety.max_power_w:
            raise SafetyLimitError(f"Power {numeric} W exceeds policy max {self.safety.max_power_w} W")
        return numeric

    def _require_output_enable_allowed(self, *, confirm: bool) -> None:
        if not confirm and not self.dry_run and not self.safety.unsafe_allow_output_on_without_confirm:
            raise OutputEnableConfirmationRequired("output_on(confirm=True) is required for real output enable")
        if self.safety.require_output_enable_permission and not self.allow_output_enable:
            raise OutputEnableNotAllowedError("allow_output_enable=True is required before output can be enabled")
        if self.safety.require_limits_before_output_on:
            missing: list[str] = []
            if self._voltage_setpoint is None:
                missing.append("voltage setpoint")
            if self._current_setpoint is None:
                missing.append("current/current-limit setpoint")
            if self.safety.max_power_w is not None and self._power_limit is None:
                missing.append("power limit")
            if missing:
                raise OutputEnableNotAllowedError("Cannot enable output before configuring " + ", ".join(missing))

    # ------------------------------------------------------------------
    # IEEE-488 and system wrappers
    # ------------------------------------------------------------------
    def idn(self) -> str:
        """Query *IDN?."""
        return str(self.query("*IDN?"))

    def reset(self, *, confirm: bool = True) -> None:
        """Send *RST. Does not enable output after reset."""
        if not confirm:
            raise OutputEnableConfirmationRequired("reset(confirm=True) is required because *RST can change state")
        self.write("*RST", check_errors=False, confirm=True)
        if self.strict:
            self.raise_on_error()
        self._voltage_setpoint = None
        self._current_setpoint = None
        self._power_limit = None

    def clear_status(self) -> None:
        self.write("*CLS", check_errors=False)

    def self_test(self) -> int:
        return int(self.query("*TST?", cast=int))

    def operation_complete(self) -> bool:
        return bool(int(self.query("*OPC?", cast=str)))

    def wait(self) -> None:
        self.write("*WAI", check_errors=False)

    def save_state(self, slot: int, *, confirm: bool = False) -> None:
        if not confirm:
            raise OutputEnableConfirmationRequired("save_state(confirm=True) is required because *SAV may save unsafe state")
        self.write(f"*SAV {int(slot)}", confirm=True)

    def recall_state(self, slot: int, *, confirm: bool = False) -> None:
        if not confirm:
            raise OutputEnableConfirmationRequired("recall_state(confirm=True) is required because *RCL may restore unsafe state")
        self.write(f"*RCL {int(slot)}", confirm=True)
        # Do not trust internal cached limits after recall.
        self._voltage_setpoint = None
        self._current_setpoint = None
        self._power_limit = None

    def set_event_status_enable(self, mask: int) -> None:
        self.write(f"*ESE {int(mask)}")

    def get_event_status_enable(self) -> int:
        return int(self.query("*ESE?", cast=int))

    def get_event_status_register(self) -> int:
        return int(self.query("*ESR?", cast=int))

    def set_service_request_enable(self, mask: int) -> None:
        self.write(f"*SRE {int(mask)}")

    def get_service_request_enable(self) -> int:
        return int(self.query("*SRE?", cast=int))

    def get_status_byte(self) -> int:
        return int(self.query("*STB?", cast=int))

    def trigger(self) -> None:
        self.write("*TRG")

    def set_power_on_status_clear(self, state: bool) -> None:
        self.write(f"*PSC {to_bool(state)}")

    def get_power_on_status_clear(self) -> bool:
        return bool(self.query("*PSC?", cast=bool))

    def set_remote(self) -> None:
        self.write("SYST:REM")

    def set_local(self) -> None:
        self.write("SYST:LOC")

    def set_remote_with_lock(self) -> None:
        self.write("SYST:RWL")

    def get_scpi_version(self) -> str:
        return str(self.query("SYST:VERS?"))

    def clear_system_errors(self) -> None:
        self.write("SYST:CLE", check_errors=False)

    def beep(self) -> None:
        self.write("SYST:BEEP:IMM")

    def set_beeper(self, enabled: bool) -> None:
        self.write(f"SYST:BEEP:STAT {to_bool(enabled)}")

    def get_beeper(self) -> bool:
        return bool(self.query("SYST:BEEP:STAT?", cast=bool))

    def set_power_on_setup(self, mode: str) -> None:
        self.write(f"SYST:POS {mode}")

    def get_power_on_setup(self) -> str:
        return str(self.query("SYST:POS?"))

    def set_date(self, year: int, month: int, day: int) -> None:
        self.write(f"SYST:DATE {int(year)},{int(month)},{int(day)}")

    def get_date(self) -> tuple[int, int, int]:
        values = [int(x) for x in str(self.query("SYST:DATE?")).split(",")]
        return cast(tuple[int, int, int], tuple(values[:3]))

    def set_time(self, hour: int, minute: int, second: int) -> None:
        self.write(f"SYST:TIME {int(hour)},{int(minute)},{int(second)}")

    def get_time(self) -> tuple[int, int, int]:
        values = [int(x) for x in str(self.query("SYST:TIME?")).split(",")]
        return cast(tuple[int, int, int], tuple(values[:3]))

    # ------------------------------------------------------------------
    # Source/output high-level wrappers
    # ------------------------------------------------------------------
    def configure_cv(self, voltage: float, current_limit: float, power_limit: float | None = None) -> None:
        self.set_function("VOLT")
        self.set_voltage(voltage)
        self.set_current_limit(current_limit)
        if power_limit is not None:
            self.set_power_limit(power_limit)

    def configure_cc(self, current: float, voltage_limit: float, power_limit: float | None = None) -> None:
        self.set_function("CURR")
        self.set_current(current)
        self.set_voltage_limit(voltage_limit)
        if power_limit is not None:
            self.set_power_limit(power_limit)

    def set_function(self, mode: str) -> None:
        self.write(f"SOUR:FUNC {mode}")

    def get_function(self) -> str:
        return str(self.query("SOUR:FUNC?"))

    def set_function_mode(self, mode: str) -> None:
        self.write(f"SOUR:FUNC:MODE {mode}")

    def get_function_mode(self) -> str:
        return str(self.query("SOUR:FUNC:MODE?"))

    def set_voltage(self, value: float | str) -> None:
        numeric = self._check_voltage_limit(value)
        self.write(f"SOUR:VOLT {format_float(value)}")
        if numeric is not None:
            self._voltage_setpoint = numeric

    def get_voltage(self, selector: str | None = None) -> float:
        return self._query_float_selector("SOUR:VOLT?", selector)

    def set_current(self, value: float | str) -> None:
        numeric = self._check_current_limit(value)
        self.write(f"SOUR:CURR {format_float(value)}")
        if numeric is not None:
            self._current_setpoint = numeric

    def get_current(self, selector: str | None = None) -> float:
        return self._query_float_selector("SOUR:CURR?", selector)

    def set_resistance(self, value: float | str) -> None:
        self.write(f"SOUR:RES {format_float(value)}")

    def get_resistance(self, selector: str | None = None) -> float:
        return self._query_float_selector("SOUR:RES?", selector)

    def set_voltage_slew(self, value: float | str) -> None:
        self.write(f"SOUR:VOLT:SLEW {format_float(value)}")

    def set_voltage_slew_positive(self, value: float | str) -> None:
        self.write(f"SOUR:VOLT:SLEW:POS {format_float(value)}")

    def set_voltage_slew_negative(self, value: float | str) -> None:
        self.write(f"SOUR:VOLT:SLEW:NEG {format_float(value)}")

    def set_current_slew(self, value: float | str) -> None:
        self.write(f"SOUR:CURR:SLEW {format_float(value)}")

    def set_current_slew_positive(self, value: float | str) -> None:
        self.write(f"SOUR:CURR:SLEW:POS {format_float(value)}")

    def set_current_slew_negative(self, value: float | str) -> None:
        self.write(f"SOUR:CURR:SLEW:NEG {format_float(value)}")

    def set_voltage_limit(self, value: float | str) -> None:
        numeric = self._check_voltage_limit(value)
        self.write(f"SOUR:VOLT:LIM {format_float(value)}")
        if numeric is not None and self._voltage_setpoint is None:
            self._voltage_setpoint = numeric

    def get_voltage_limit(self, selector: str | None = None) -> float:
        return self._query_float_selector("SOUR:VOLT:LIM?", selector)

    def set_current_limit(self, value: float | str) -> None:
        numeric = self._check_current_limit(value)
        self.write(f"SOUR:CURR:LIM {format_float(value)}")
        if numeric is not None:
            self._current_setpoint = numeric

    def get_current_limit(self, selector: str | None = None) -> float:
        return self._query_float_selector("SOUR:CURR:LIM?", selector)

    def set_power_limit(self, value: float | str) -> None:
        numeric = self._check_power_limit(value)
        self.write(f"SOUR:POW:LIM {format_float(value)}")
        if numeric is not None:
            self._power_limit = numeric

    def get_power_limit(self, selector: str | None = None) -> float:
        return self._query_float_selector("SOUR:POW:LIM?", selector)

    def output_on(self, confirm: bool = False) -> None:
        self._require_output_enable_allowed(confirm=confirm)
        self.write("OUTP ON", confirm=True)
        self._last_output_on_time = time.monotonic()

    def output_off(self, verify: bool | None = None) -> None:
        self.write("OUTP OFF", check_errors=self.strict)
        self._last_output_on_time = None
        if verify is None:
            verify = self.safety.verify_output_off
        if verify and not self.verify_output_is_safe():
            raise OutputNotSafeError("Output voltage did not decay below configured safety threshold")

    def set_output(self, enabled: bool, *, confirm: bool = False) -> None:
        if enabled:
            self.output_on(confirm=confirm)
        else:
            self.output_off(verify=False)

    def get_output(self) -> bool:
        return bool(self.query("OUTP?", cast=bool))

    def clear_output_protection(self, confirm: bool = False) -> None:
        if not confirm:
            raise OutputEnableConfirmationRequired("clear_output_protection(confirm=True) is required")
        self.write("OUTP:PROT:CLE", confirm=True)

    def emergency_stop(self) -> None:
        try:
            self._write_no_check("OUTP OFF")
        finally:
            try:
                self.check_errors()
            except Exception:
                pass

    def verify_output_is_safe(self, timeout_s: float | None = None) -> bool:
        if self.dry_run:
            return True
        timeout_s = self.safety.output_off_verify_timeout_s if timeout_s is None else timeout_s
        threshold = self.safety.output_off_verify_voltage_threshold_v
        deadline = time.monotonic() + timeout_s
        while time.monotonic() <= deadline:
            try:
                if abs(self.measure_voltage()) <= threshold:
                    return True
            except Exception:
                pass
            time.sleep(0.2)
        return False

    def set_output_inhibit_mode(self, mode: str) -> None:
        self.write(f"OUTP:INH:MODE {mode}")

    def get_output_inhibit_mode(self) -> str:
        return str(self.query("OUTP:INH:MODE?"))

    def set_output_power_on_state(self, state: str, *, confirm: bool = False) -> None:
        if state.strip().upper() in {"LAST_ON", "ON"}:
            self._require_output_enable_allowed(confirm=confirm)
        self.write(f"OUTP:PON:STAT {state}", confirm=confirm)

    def get_output_power_on_state(self) -> str:
        return str(self.query("OUTP:PON:STAT?"))

    def set_output_watchdog(self, enabled: bool) -> None:
        self.write(f"OUTP:PROT:WDOG {to_bool(enabled)}")

    def get_output_watchdog(self) -> bool:
        return bool(self.query("OUTP:PROT:WDOG?", cast=bool))

    def set_output_watchdog_delay(self, delay_s: float | str) -> None:
        self.write(f"OUTP:PROT:WDOG:DEL {format_float(delay_s)}")

    def get_output_watchdog_delay(self, selector: str | None = None) -> float:
        return self._query_float_selector("OUTP:PROT:WDOG:DEL?", selector)

    def set_output_delay_rise(self, delay_s: float | str) -> None:
        self.write(f"OUTP:DEL:RISE {format_float(delay_s)}")

    def get_output_delay_rise(self, selector: str | None = None) -> float:
        return self._query_float_selector("OUTP:DEL:RISE?", selector)

    def set_output_delay_fall(self, delay_s: float | str) -> None:
        self.write(f"OUTP:DEL:FALL {format_float(delay_s)}")

    def get_output_delay_fall(self, selector: str | None = None) -> float:
        return self._query_float_selector("OUTP:DEL:FALL?", selector)

    # Protection generic wrappers
    def set_voltage_protection(self, level: float | str) -> None:
        self._check_voltage_limit(level)
        self.write(f"SOUR:VOLT:PROT {format_float(level)}")

    def get_voltage_protection(self) -> float:
        return float(self.query("SOUR:VOLT:PROT?", cast=float))

    def set_voltage_protection_state(self, enabled: bool) -> None:
        self.write(f"SOUR:VOLT:PROT:STAT {to_bool(enabled)}")

    def get_voltage_protection_state(self) -> bool:
        return bool(self.query("SOUR:VOLT:PROT:STAT?", cast=bool))

    def set_current_protection(self, level: float | str) -> None:
        self._check_current_limit(level)
        self.write(f"SOUR:CURR:PROT {format_float(level)}")

    def get_current_protection(self) -> float:
        return float(self.query("SOUR:CURR:PROT?", cast=float))

    def set_current_protection_state(self, enabled: bool) -> None:
        self.write(f"SOUR:CURR:PROT:STAT {to_bool(enabled)}")

    def get_current_protection_state(self) -> bool:
        return bool(self.query("SOUR:CURR:PROT:STAT?", cast=bool))

    def set_power_protection(self, level: float | str) -> None:
        self._check_power_limit(level)
        self.write(f"SOUR:POW:PROT {format_float(level)}")

    def get_power_protection(self) -> float:
        return float(self.query("SOUR:POW:PROT?", cast=float))

    def set_power_protection_state(self, enabled: bool) -> None:
        self.write(f"SOUR:POW:PROT:STAT {to_bool(enabled)}")

    def get_power_protection_state(self) -> bool:
        return bool(self.query("SOUR:POW:PROT:STAT?", cast=bool))

    def _query_float_selector(self, command: str, selector: str | None = None) -> float:
        return float(self.query(command if selector is None else f"{command} {selector}", cast=float))

    # ------------------------------------------------------------------
    # Measurements / fetch / format
    # ------------------------------------------------------------------
    def measure_voltage(self) -> float:
        return float(self.query("MEAS:VOLT?", cast=float))

    def measure_current(self) -> float:
        return float(self.query("MEAS:CURR?", cast=float))

    def measure_power(self) -> float:
        return float(self.query("MEAS:POW?", cast=float))

    def measure_scalar(self) -> list[float]:
        return parse_csv_floats(str(self.query("MEAS?")))

    def fetch_voltage(self) -> float:
        return float(self.query("FETC:VOLT?", cast=float))

    def fetch_current(self) -> float:
        return float(self.query("FETC:CURR?", cast=float))

    def fetch_power(self) -> float:
        return float(self.query("FETC:POW?", cast=float))

    def fetch_scalar(self) -> list[float]:
        return parse_csv_floats(str(self.query("FETC?")))

    def measure_array_voltage(self) -> bytes | list[float]:
        return maybe_parse_ascii_or_block(self.query_raw("MEAS:ARR:VOLT?"))

    def measure_array_current(self) -> bytes | list[float]:
        return maybe_parse_ascii_or_block(self.query_raw("MEAS:ARR:CURR?"))

    def measure_array_power(self) -> bytes | list[float]:
        return maybe_parse_ascii_or_block(self.query_raw("MEAS:ARR:POW?"))

    def fetch_array_voltage(self) -> bytes | list[float]:
        return maybe_parse_ascii_or_block(self.query_raw("FETC:ARR:VOLT?"))

    def fetch_array_current(self) -> bytes | list[float]:
        return maybe_parse_ascii_or_block(self.query_raw("FETC:ARR:CURR?"))

    def fetch_array_power(self) -> bytes | list[float]:
        return maybe_parse_ascii_or_block(self.query_raw("FETC:ARR:POW?"))

    def set_format(self, mode: str) -> None:
        self.write(f"FORM {mode}")

    def get_format(self) -> str:
        return str(self.query("FORM?"))

    # ------------------------------------------------------------------
    # DLOG / ELOG
    # ------------------------------------------------------------------
    def configure_dlog(self, period: float, time_s: float, current: bool = True, voltage: bool = True, peak: bool = False) -> None:
        self.write(f"SENS:DLOG:FUNC:CURR {to_bool(current)}")
        self.write(f"SENS:DLOG:FUNC:VOLT {to_bool(voltage)}")
        self.write(f"SENS:DLOG:FUNC:PEAK {to_bool(peak)}")
        self.write(f"SENS:DLOG:PER {format_float(period)}")
        self.write(f"SENS:DLOG:TIME {format_float(time_s)}")

    def start_dlog(self) -> None:
        self.write("INIT:DLOG")

    def abort_dlog(self) -> None:
        self.write("ABOR:ACQ")

    def get_dlog_state(self) -> str:
        return str(self.query("DLOG:STAT?"))

    def trigger_dlog(self) -> None:
        self.write("TRIG:DLOG")

    def configure_elog(self, period: float, time_s: float | None = None, current: bool = True, voltage: bool = True, peak: bool = False) -> None:
        self.write(f"SENS:ELOG:FUNC:CURR {to_bool(current)}")
        self.write(f"SENS:ELOG:FUNC:VOLT {to_bool(voltage)}")
        self.write(f"SENS:ELOG:FUNC:PEAK {to_bool(peak)}")
        self.write(f"SENS:ELOG:PER {format_float(period)}")
        if time_s is not None:
            self.write(f"SENS:ELOG:TIME {format_float(time_s)}")

    def start_elog(self) -> None:
        self.write("INIT:ELOG")

    def abort_elog(self) -> None:
        self.write("ABOR:ACQ")

    def get_elog_state(self) -> str:
        return str(self.query("ELOG:STAT?"))

    def trigger_elog(self) -> None:
        self.write("TRIG:ELOG")

    def fetch_elog_array_data_raw(self) -> bytes:
        return self.query_raw("FETC:ELOG:ARR:DATA?")

    def fetch_elog_array_data(self, format: str = "ASCII") -> bytes | list[float]:
        self.set_format(format)
        data = self.fetch_elog_array_data_raw()
        return maybe_parse_ascii_or_block(data)

    # ------------------------------------------------------------------
    # ARB/list convenience helpers
    # ------------------------------------------------------------------
    def configure_list_voltage(self, steps: list[ArbStep], repeat_count: int = 1, terminate_last: bool = True) -> None:
        self.write("ARB:FUNC:TYPE VOLT")
        self.write(f"ARB:COUN {int(repeat_count)}")
        self.write(f"ARB:TERM:LAST {'ON' if terminate_last else 'OFF'}")
        self.write(f"ARB:UDEF:COUN {len(steps)}")
        for i, step in enumerate(steps, start=1):
            self._check_voltage_limit(step.level)
            self.write(f"ARB:UDEF:LEV {i},{format_float(step.level)}")
            self.write(f"ARB:UDEF:DWEL {i},{format_float(step.dwell_s)}")
            if step.slew is not None:
                self.write(f"ARB:UDEF:SLEW {i},{format_float(step.slew)}")
            if step.trigout is not None:
                self.write(f"ARB:UDEF:TRIG {step.trigout}")

    def configure_list_current(self, steps: list[ArbStep], repeat_count: int = 1, terminate_last: bool = True) -> None:
        self.write("ARB:FUNC:TYPE CURR")
        self.write(f"ARB:COUN {int(repeat_count)}")
        self.write(f"ARB:TERM:LAST {'ON' if terminate_last else 'OFF'}")
        self.write(f"ARB:UDEF:COUN {len(steps)}")
        for i, step in enumerate(steps, start=1):
            self._check_current_limit(step.level)
            self.write(f"ARB:UDEF:LEV {i},{format_float(step.level)}")
            self.write(f"ARB:UDEF:DWEL {i},{format_float(step.dwell_s)}")
            if step.slew is not None:
                self.write(f"ARB:UDEF:SLEW {i},{format_float(step.slew)}")
            if step.trigout is not None:
                self.write(f"ARB:UDEF:TRIG {step.trigout}")

    def start_arb(self, wait_for_trigger: bool = True, *, confirm: bool = False) -> None:
        if not confirm:
            raise OutputEnableConfirmationRequired("start_arb(confirm=True) is required")
        self.write(f"INIT:CONT:ARB {to_bool(not wait_for_trigger)}")
        self.write("INIT:ARB", confirm=True)

    def trigger_arb(self) -> None:
        self.write("TRIG:ARB")

    def pause_arb(self, enabled: bool) -> None:
        self.write(f"ARB:PAUS:STAT {to_bool(enabled)}")

    def abort_arb(self) -> None:
        self.write("ABOR:ARB")

    def save_arb(self, slot: int, *, confirm: bool = False) -> None:
        if not confirm:
            raise OutputEnableConfirmationRequired("save_arb(confirm=True) is required")
        self.write(f"ARB:SAVE {int(slot)}", confirm=True)

    def recall_arb(self, slot: int, *, confirm: bool = False) -> None:
        if not confirm:
            raise OutputEnableConfirmationRequired("recall_arb(confirm=True) is required")
        self.write(f"ARB:REC {int(slot)}", confirm=True)

    def get_arb_execution_state(self) -> str:
        return str(self.query("ARB:EXE:STAT?"))

    # ------------------------------------------------------------------
    # Battery mode
    # ------------------------------------------------------------------
    def set_battery_charge_voltage(self, value: float | str) -> None:
        self._check_voltage_limit(value)
        self.write(f"BATT:CHAR:VOLT {format_float(value)}")

    def get_battery_charge_voltage(self, selector: str | None = None) -> float:
        return self._query_float_selector("BATT:CHAR:VOLT?", selector)

    def set_battery_charge_current(self, value: float | str) -> None:
        self._check_current_limit(value)
        self.write(f"BATT:CHAR:CURR {format_float(value)}")

    def get_battery_charge_current(self, selector: str | None = None) -> float:
        return self._query_float_selector("BATT:CHAR:CURR?", selector)

    def set_battery_shutdown_voltage(self, value: float | str) -> None:
        self._check_voltage_limit(value)
        self.write(f"BATT:SHUT:VOLT {format_float(value)}")

    def get_battery_shutdown_voltage(self, selector: str | None = None) -> float:
        return self._query_float_selector("BATT:SHUT:VOLT?", selector)

    def set_battery_shutdown_current(self, value: float | str) -> None:
        self._check_current_limit(value)
        self.write(f"BATT:SHUT:CURR {format_float(value)}")

    def get_battery_shutdown_current(self, selector: str | None = None) -> float:
        return self._query_float_selector("BATT:SHUT:CURR?", selector)

    def set_battery_shutdown_capacity(self, value: float | str) -> None:
        self.write(f"BATT:SHUT:CAP {format_float(value)}")

    def get_battery_shutdown_capacity(self, selector: str | None = None) -> float:
        return self._query_float_selector("BATT:SHUT:CAP?", selector)

    def set_battery_shutdown_time(self, value: float | str) -> None:
        self.write(f"BATT:SHUT:TIME {format_float(value)}")

    def get_battery_shutdown_time(self, selector: str | None = None) -> float:
        return self._query_float_selector("BATT:SHUT:TIME?", selector)

    def set_battery_mode(self, mode: str, *, confirm: bool = False) -> None:
        if not confirm:
            raise OutputEnableConfirmationRequired("set_battery_mode(confirm=True) is required until verified on hardware")
        self.write(f"BATT:MODE {mode}", confirm=True)

    def run_battery_mode(self, *, confirm: bool = False) -> None:
        self.set_battery_mode("CHAR", confirm=confirm)

    def stop_battery_mode(self) -> None:
        self.output_off(verify=False)

    # ------------------------------------------------------------------
    # Digital IO / status
    # ------------------------------------------------------------------
    def io_select(self, bank: int) -> None:
        self.write(f"IO:SEL {int(bank)}")

    def io_selected(self) -> int:
        return int(self.query("IO:SEL?", cast=int))

    def set_io_direction(self, channel: int, output: bool) -> None:
        self.write(f"IO:DIR {int(channel)},{to_bool(output)}")

    def get_io_direction(self, channel: int) -> bool:
        return bool(self.query(f"IO:DIR? {int(channel)}", cast=bool))

    def set_io_reverse(self, channel: int, enabled: bool) -> None:
        self.write(f"IO:REV {int(channel)},{to_bool(enabled)}")

    def get_io_reverse(self, channel: int) -> bool:
        return bool(self.query(f"IO:REV? {int(channel)}", cast=bool))

    def set_io_pwm_enable(self, channel: int, enabled: bool) -> None:
        self.write(f"IO:PWM:ENAB {int(channel)},{to_bool(enabled)}")

    def set_io_pwm_frequency(self, channel: int, frequency: float | str) -> None:
        self.write(f"IO:PWM:FREQ {int(channel)},{format_float(frequency)}")

    def set_io_pwm_duty(self, channel: int, duty_percent: int) -> None:
        self.write(f"IO:PWM:DUTY {int(channel)},{int(duty_percent)}")

    def set_io_pulse_width(self, channel: int, width_s: float | str) -> None:
        self.write(f"IO:PULS:WIDT {int(channel)},{format_float(width_s)}")

    def set_io_type(self, channel: int, io_type: str) -> None:
        self.write(f"IO:TYPE {int(channel)},{io_type}")

    def set_io_trigger_type(self, trigger_type: str) -> None:
        self.write(f"IO:TRIG:TYPE {trigger_type}")

    def set_io_trigger_source(self, source: str) -> None:
        # Manual spelling uses TRIGer with one g in this command family.
        self.write(f"IO:TRIGer:SOUR {source}")

    def set_io_output_level(self, channel: int, level: str) -> None:
        self.write(f"IO:OUTP:LEV {int(channel)},{level}")

    def get_io_input_level(self, channel: int) -> str:
        return str(self.query(f"IO:INP:LEV? {int(channel)}"))

    def status_questionable_event(self) -> int:
        return int(self.query("STAT:QUES:EVEN?", cast=int))

    def status_questionable_condition(self) -> int:
        return int(self.query("STAT:QUES:COND?", cast=int))

    def status_operation_event(self) -> int:
        return int(self.query("STAT:OPER:EVEN?", cast=int))

    def status_operation_condition(self) -> int:
        return int(self.query("STAT:OPER:COND?", cast=int))

    def status_preset(self) -> None:
        self.write("STAT:PRES")

    def set_status_enable(self, group: Literal["QUES", "OPER"], mask: int) -> None:
        self.write(f"STAT:{group}:ENAB {int(mask)}")

    def get_status_enable(self, group: Literal["QUES", "OPER"]) -> int:
        return int(self.query(f"STAT:{group}:ENAB?", cast=int))

    # ------------------------------------------------------------------
    # Parallel and sense helpers
    # ------------------------------------------------------------------
    def set_parallel_role(self, role: str) -> None:
        self.write(f"PAR:ROLE {role}")

    def get_parallel_role(self) -> str:
        return str(self.query("PAR:ROLE?"))

    def set_parallel_number(self, number: int) -> None:
        self.write(f"PAR:NUMB {int(number)}")

    def get_parallel_number(self) -> int:
        return int(self.query("PAR:NUMB?", cast=int))

    def set_remote_sense(self, enabled: bool) -> None:
        self.write(f"SOUR:REM:SENS {to_bool(enabled)}")

    def get_remote_sense(self) -> bool:
        return bool(self.query("SOUR:REM:SENS?", cast=bool))


__all__ = ["ITM3900D", "ArbStep"]
