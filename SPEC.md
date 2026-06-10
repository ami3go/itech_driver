# Software Task: Production-Grade IT-M3900D PyVISA Driver

Source manual: **ITECH IT-M3900D Series Programming Guide**, Version **V1.5 / 07-2025**.

Document version: **v1.3 final production-code-generation cleanup patch**.

This document is a task/specification for generating a production-grade Python driver package for the **IT-M3900D Series High Power Programmable DC Power Supply** using **PyVISA**. It supersedes the previous v1.0/v1.1/v1.2 task by adding stronger safety interlocks, command-catalog metadata, transport locking, hardware-in-loop acceptance tests, missing query coverage from command-page `Syntax` / `Query Syntax` sections, explicit guarded-command metadata, corrected newline terminator examples, final command-catalog fixes, and cleanup of Appendix A/B structure required before production code generation.

---


## Change History

| Version | Date | Notes |
|---|---:|---|
| v1.3 | 2026-06-09 | Moved `FORMat[:data]?` into Appendix B; removed misplaced Appendix C `FORMat` section; added missing Appendix A headings for configurable IO, IEEE-488 common commands, and FORMat; strengthened `output_on(confirm=True)` safety gate; added confirmation-required unit test; made supplemental count advisory. |
| v1.2 | 2026-06-09 | Fixed newline terminator examples; added guarded/dangerous command metadata; added missing `FORMat[:data]?`; added output subsystem safety queries; removed duplicate/artifact supplemental entries; added catalog tests for these items. |
| v1.1 | 2026-06-09 | Added production safety policy, transport locking, command metadata, and HIL acceptance matrix. |
| v1.0 | 2026-06-09 | Initial PyVISA USB/Ethernet driver generation task. |

---

## 1. Goal

Create a typed, tested, safe-by-default Python package that controls the ITECH IT-M3900D family through SCPI over PyVISA.

The driver shall support:

- USB-TMC through PyVISA.
- Ethernet through PyVISA using both VXI-11 resources and raw TCP socket resources.
- A low-level SCPI API for every command in the programming guide.
- High-level convenience APIs for normal power-supply workflows: connection, identification, reset, remote/local control, voltage/current/power setup, protection, output control, measurement, fetch, DLOG/ELOG, ARB/list, battery mode, digital IO, status, and error handling.
- Production safety suitable for automated lab/test-rack use with high-power DC supplies.

The manual requires newline-terminated SCPI messages and warns that full query results must be read before another command is sent. The implementation shall serialize all command/query traffic and shall never pipeline queries unless explicitly implemented and tested.

---

## 2. Production-Grade Definition

The generated package is production-grade only when all items below are true:

1. **Safe by default**: no constructor, discovery, connect, reset, reconnect, or context-manager entry can enable output.
2. **Explicit output enable**: output-on requires an explicit method call and, by default, a configured safety policy that allows output enable.
3. **Configurable safety limits**: voltage, current, power, and optional energy/time limits are enforced in software before commands are sent.
4. **Transport-safe**: all PyVISA I/O is protected by a re-entrant lock; one command/query is in flight at a time.
5. **Complete command coverage**: every command in Appendix A and every supplemental query in Appendix B is represented in `command_catalog.py`.
6. **Error-aware**: strict mode checks `SYST:ERR?` after setters and raises meaningful exceptions.
7. **Recoverable**: timeout, query-interrupted, socket disconnect, and VISA session errors have defined recovery behavior.
8. **Typed and documented**: public API is typed, documented, and includes exact SCPI command strings in docstrings.
9. **Tested without hardware**: mock VISA tests cover formatting, parsing, safety behavior, command coverage, and error paths.
10. **Hardware verified**: USB, VXI-11, socket, DLOG/ELOG, ARB/list, and protection tests have a documented manual/automated hardware verification status.

---

## 3. Deliverables

Create this Python package layout:

```text
itm3900d/
  pyproject.toml
  README.md
  CHANGELOG.md
  LICENSE
  itm3900d/
    __init__.py
    instrument.py
    command_catalog.py
    transport.py
    safety.py
    status.py
    types.py
    exceptions.py
    parsers.py
    py.typed
  examples/
    usb_basic.py
    ethernet_vxi11_basic.py
    ethernet_socket_basic.py
    cv_mode_safe.py
    cc_mode_safe.py
    battery_charge.py
    dlog_fetch.py
    elog_fetch_binary.py
    arb_list_voltage.py
    digital_io.py
  tests/
    test_command_formatting.py
    test_boolean_conversion.py
    test_catalog_coverage.py
    test_pyvisa_mock.py
    test_safety_policy.py
    test_error_queue.py
    test_binary_block_parser.py
    test_resource_generation.py
    test_no_output_on_during_connect.py
    test_guarded_command_metadata.py
    test_output_on_confirmation_required.py
    test_output_query_catalog.py
    test_format_query_catalog.py
  scripts/
    hil_smoke_usb.py
    hil_smoke_ethernet_vxi11.py
    hil_smoke_ethernet_socket.py
    hil_elog_binary.py
    hil_arb_list.py
```

Main import:

```python
from itm3900d import ITM3900D
```

---

## 4. Dependencies

Required:

```text
python >= 3.10
pyvisa
```

Optional:

```text
pyvisa-py        # fallback backend when NI-VISA is unavailable
numpy            # optional array/log parsing
pytest           # unit tests
ruff             # linting
mypy             # type checking
typing_extensions # only if needed for older Python minor versions
```

---

## 5. Connection and Transport Requirements

### 5.1 Constructor

```python
def __init__(
    self,
    resource: str | None = None,
    *,
    ip: str | None = None,
    port: int = 5025,
    lan_mode: str = "auto",   # "auto", "vxi11", "socket"
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
    safety: "SafetyPolicy | None" = None,
    allow_output_enable: bool = False,
    scpi_logger: "Callable[[ScpiLogRecord], None] | None" = None,
): ...
```

Constructor shall not open output and shall not apply unsafe settings.

### 5.2 USB Support

Implement:

```python
ITM3900D.list_resources() -> list[str]
ITM3900D.find_usb(idn_regex: str | None = None) -> list[str]
ITM3900D.open_usb(resource: str | None = None, **kwargs) -> ITM3900D
```

Requirements:

- Use `pyvisa.ResourceManager(backend)`.
- Search `USB?*::INSTR` resources.
- If VID/PID are unknown, identify compatible devices by `*IDN?` and match `ITECH`, `IT-M3900D`, `IT39`, or a user-provided regex.
- Do not hard-code VID/PID unless verified on real hardware.
- Discovery shall not send any output-enable command.

### 5.3 Ethernet/LAN Support

Implement:

```python
ITM3900D.open_ethernet(ip: str, port: int = 5025, lan_mode: str = "auto", **kwargs) -> ITM3900D
```

Resource generation:

- `lan_mode="vxi11"`: `TCPIP0::<ip>::inst0::INSTR`
- `lan_mode="socket"`: `TCPIP0::<ip>::<port>::SOCKET`
- `lan_mode="auto"`: try VXI-11 first, then raw socket.

Socket requirements:

```python
instrument.write_termination = "\n"
instrument.read_termination = "\n"
```

### 5.4 Remote Mode

After a successful connection, if `auto_remote=True`, send:

```text
SYST:REM
```

If `lock_front_panel=True`, send:

```text
SYST:RWL
```

When closing, optionally return to local mode only if configured:

```python
return_local_on_close: bool = False
```

---

## 6. Safety Requirements

This instrument can output dangerous voltage/current. The driver shall prioritize fail-safe behavior over convenience.

### 6.1 Safety Policy

Implement:

```python
@dataclass(frozen=True)
class SafetyPolicy:
    max_voltage_v: float | None = None
    max_current_a: float | None = None
    max_power_w: float | None = None
    max_output_on_time_s: float | None = None
    require_limits_before_output_on: bool = True
    require_output_enable_permission: bool = True
    output_off_on_close: bool = False
    output_off_on_exception: bool = False
    verify_output_off: bool = True
    output_off_verify_voltage_threshold_v: float = 1.0
    output_off_verify_timeout_s: float = 10.0
    unsafe_allow_output_on_without_confirm: bool = False  # test-only/dry-run-only escape hatch
```

Mandatory behavior:

- No automatic output ON in `__init__`, `open()`, `connect()`, discovery, reset, reconnect, or `__enter__`.
- `output_on()` must check `allow_output_enable` and `SafetyPolicy` limits.
- `output_on(confirm=False)` shall always raise `OutputEnableConfirmationRequired` for real hardware output enable. Setting `allow_output_enable=True` alone is not enough to energize the output.
- The only allowed bypass for `confirm=True` is `dry_run=True` or an explicitly named unsafe test override: `SafetyPolicy.unsafe_allow_output_on_without_confirm=True`. Production examples and production code paths shall keep this override disabled.
- `output_on()` must refuse to run if configured voltage/current/power is unknown and `require_limits_before_output_on=True`.
- `set_voltage`, `set_current`, `set_current_limit`, `set_voltage_limit`, `set_power_limit`, and protection-level methods must validate against configured safety limits before sending SCPI.
- `reset()` must not be followed by output ON.
- `emergency_stop()` shall send `OUTP 0`, then read status/error queue where possible.
- `close()` shall not change output state unless `output_off_on_close=True`.
- Hardware examples shall require explicit user confirmation before output ON.

### 6.2 Suggested Safe High-Level Methods

```python
configure_cv(voltage: float, current_limit: float, power_limit: float | None = None) -> None
configure_cc(current: float, voltage_limit: float, power_limit: float | None = None) -> None
output_on(confirm: bool = False) -> None
output_off(verify: bool | None = None) -> None
emergency_stop() -> None
verify_output_is_safe(timeout_s: float | None = None) -> bool
```

`confirm=True` is mandatory for real output enable. It is only a software guard and is not a replacement for external safety interlocks. The driver shall raise `OutputEnableConfirmationRequired` when `output_on(confirm=False)` is called unless `dry_run=True` or the explicitly unsafe test override is enabled.


### 6.3 Guarded and Dangerous SCPI Commands

The command catalog shall classify commands using `safety_class` metadata:

- `safe`: read-only queries or settings that cannot energize output or mask a protection state.
- `guarded`: commands that can change operating mode, restore state, clear protection, start programmed behavior, or indirectly create hazardous output.
- `dangerous`: commands that can directly energize output or configure the instrument to energize output automatically after a later event.

The following commands and command/value combinations must be marked at least `guarded`; those marked `dangerous` require explicit safety-policy permission plus confirmation in high-level helpers:

| Command / combination | Minimum class | Required behavior |
|---|---:|---|
| `OUTPut[:STATe] 1` / `OUTPut ON` | dangerous | Must go through `output_on(confirm=True)` or equivalent guarded path. |
| `OUTPut:PROTection:CLEar` | guarded | Must not be called silently after a trip; require explicit user/action context. |
| `OUTPut:PON:STATe LAST_ON` | dangerous | Disable by default; require explicit override because output can re-enable after power cycle. |
| `*RCL <slot>` | guarded | May restore unsafe voltage/current/output state; verify output state and limits after recall. |
| `*SAV <slot>` | guarded | May save unsafe power-on/recall behavior; require explicit user intent. |
| `*RST` | guarded | Must never be followed by automatic output enable; re-apply safety state after reset. |
| `INITiate[:IMMediate]:ARB` / `INIT:ARB` | guarded | May start programmed source behavior; require configured limits and explicit start method. |
| `BATT:MODE CHAR` or battery-mode start helper | guarded | Manual-example/compatibility command until verified; check errors after use. |

Acceptance tests shall verify that every guarded/dangerous command has catalog metadata, that no generated high-level wrapper bypasses `SafetyPolicy`, and that `output_on(confirm=False)` is rejected on real/non-dry-run sessions even when `allow_output_enable=True`.

---

## 7. Core Transport API

Implement:

```python
open() -> None
close() -> None
is_open -> bool
write(command: str) -> None
query(command: str, *, cast: Callable | type = str) -> Any
read_raw() -> bytes
query_raw(command: str) -> bytes
clear() -> None
wait_opc(timeout_ms: int | None = None) -> bool
check_errors(max_reads: int = 25) -> list[InstrumentErrorRecord]
raise_on_error() -> None
```

Transport rules:

- Exactly one newline terminator per program message.
- Complete response to every query must be read before any next program message.
- All write/query/read operations must acquire the same `threading.RLock`.
- High-level wrappers shall send one SCPI command at a time unless explicitly documented.
- Low-level `write()` and `query()` may support semicolon command chaining.
- In strict mode, setters should call `check_errors()` after the write.
- Log every command/response with timestamp, transport resource, elapsed time, and exception if a logger is configured.
- Provide `dry_run=True` mode that records SCPI without opening VISA.

---

## 8. Parsing and Type Conversion

Implement robust conversion helpers:

```python
to_bool(value: bool | int | str) -> Literal["ON", "OFF"]
from_bool_response(value: str) -> bool
format_float(value: float | int | str) -> str
parse_float(value: str) -> float
parse_csv_floats(value: str) -> list[float]
parse_csv_mixed(value: str) -> list[str | float]
parse_status_register(value: str) -> int
parse_scpi_error(value: str) -> InstrumentErrorRecord
parse_definite_length_block(data: bytes) -> bytes
```

Support manual data types:

- `<NR1>` integer.
- `<NR2>` floating-point.
- `<NR3>` scientific notation.
- `<NRf>` flexible numeric.
- `<NRf+>` numeric plus `MINimum`, `MAXimum`, `DEFault`.
- `<Bool>` accepts `0`, `1`, `OFF`, `ON`; queries return `0` or `1`.
- `<CPD>` discrete character data.
- `<SPD>` quoted string program data.
- `<CRD>`, `<AARD>`, `<SRD>`, and arbitrary block responses.

---

## 9. Command Catalog Architecture

Create a machine-readable catalog in `command_catalog.py`.

```python
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
```

Requirements:

- Appendix A commands are the minimum TOC-derived baseline.
- Appendix B supplemental queries must be included because many query forms appear in command pages but not in the TOC list.
- The implementation shall parse or encode command metadata from every command page, not only the table of contents.
- Any command that lacks a high-level named wrapper must still be callable through a generated dispatch layer, e.g. `psu.scpi.<method>()` or `psu.invoke("catalog_key", ...)`.
- `test_catalog_coverage.py` must fail if a command in Appendix A or B is missing from `command_catalog.py`.
- Every wrapper docstring must include the exact SCPI command and the manual page if available.
- Guarded/dangerous command metadata is mandatory for output, protection-clear, reset, recall, save, ARB-start, and battery-mode start commands.
- `test_guarded_command_metadata.py` must fail if any known guarded/dangerous command is missing `safety_class`, confirmation, or permission metadata.
- `test_output_query_catalog.py` and `test_format_query_catalog.py` must fail if the output subsystem query commands or `FORMat[:data]?` are missing.
- `test_output_on_confirmation_required.py` must fail if `output_on(confirm=False)` can energize output on a real/non-dry-run session.

---

## 10. Public High-Level API Requirements

### 10.1 Identification and IEEE-488 Common Commands

Implement wrappers for:

```python
idn() -> str
reset() -> None
clear_status() -> None
self_test() -> int
operation_complete() -> bool
wait() -> None
save_state(slot: int) -> None
recall_state(slot: int) -> None
set_event_status_enable(mask: int) -> None
get_event_status_enable() -> int
get_event_status_register() -> int
set_service_request_enable(mask: int) -> None
get_service_request_enable() -> int
get_status_byte() -> int
trigger() -> None
set_power_on_status_clear(state: bool) -> None
get_power_on_status_clear() -> bool
```

### 10.2 System

Implement wrappers for power-on setup, SCPI version, error queue, clear, remote/local/RW lock, beeper, date/time, communication select, GPIB address, serial baud/address, and LAN IP/subnet/gateway settings.

### 10.3 Source / Output Control

Implement wrappers for all source and output commands, including:

```python
set_function(mode: str) -> None
get_function() -> str
set_function_mode(mode: str) -> None
get_function_mode() -> str
set_voltage(value: float | str) -> None
get_voltage(selector: str | None = None) -> float
set_current(value: float | str) -> None
get_current(selector: str | None = None) -> float
set_resistance(value: float | str) -> None
get_resistance(selector: str | None = None) -> float
set_voltage_slew(value: float | str) -> None
set_voltage_slew_positive(value: float | str) -> None
set_voltage_slew_negative(value: float | str) -> None
set_current_slew(value: float | str) -> None
set_current_slew_positive(value: float | str) -> None
set_current_slew_negative(value: float | str) -> None
set_voltage_limit(value: float | str) -> None
get_voltage_limit(selector: str | None = None) -> float
set_current_limit(value: float | str) -> None
get_current_limit(selector: str | None = None) -> float
set_power_limit(value: float | str) -> None
get_power_limit(selector: str | None = None) -> float
output_on(confirm: bool = False) -> None
output_off(verify: bool | None = None) -> None
set_output(enabled: bool, *, confirm: bool = False) -> None
get_output() -> bool
clear_output_protection(confirm: bool = False) -> None
set_output_inhibit_mode(mode: str) -> None
get_output_inhibit_mode() -> str
set_output_power_on_state(state: str) -> None
get_output_power_on_state() -> str
set_output_watchdog(enabled: bool) -> None
get_output_watchdog() -> bool
set_output_watchdog_delay(delay_s: float | str) -> None
get_output_watchdog_delay(selector: str | None = None) -> float
```

Also implement all over/under voltage/current/power protection state, level, delay, and warm-time wrappers where documented. Output power-on-state, inhibit, watchdog state, and watchdog delay query wrappers are required because they affect safety and recovery behavior.

### 10.4 Measurement and Fetch

Implement `MEASure` and `FETCh` wrappers for current, voltage, power, HIGH, LOW, MAXimum, MINimum, scalar tuple, and arrays.

Array and ELOG data requirements:

- Support ASCII comma-separated arrays.
- Support definite-length binary blocks.
- Expose raw byte methods for unknown/undocumented binary layouts.
- Include unit tests for empty, malformed, and partial block data.

### 10.5 DLOG / ELOG

Implement configuration, start, abort, state, trigger-source, trigger-immediate, fetch, and data-format methods.

```python
configure_dlog(period: float, time_s: float, current=True, voltage=True, peak=False) -> None
start_dlog() -> None
abort_dlog() -> None
get_dlog_state() -> str
trigger_dlog() -> None
configure_elog(period: float, time_s: float | None = None, current=True, voltage=True, peak=False) -> None
start_elog() -> None
abort_elog() -> None
get_elog_state() -> str
trigger_elog() -> None
fetch_elog_array_data(format: str = "ASCII") -> bytes | list[float]
fetch_elog_array_data_raw() -> bytes
set_format(mode: str) -> None
get_format() -> str
```

### 10.6 ARB / LIST

Implement every ARB set/query/action in the catalog and high-level helpers for list voltage/current/current-dwell operations.

```python
@dataclass
class ArbStep:
    level: float
    dwell_s: float
    slew: float | None = None
    trigout: str | None = None
```

```python
configure_list_voltage(steps: list[ArbStep], repeat_count: int = 1, terminate_last: bool = True) -> None
configure_list_current(steps: list[ArbStep], repeat_count: int = 1, terminate_last: bool = True) -> None
start_arb(wait_for_trigger: bool = True) -> None
trigger_arb() -> None
pause_arb(enabled: bool) -> None
abort_arb() -> None
save_arb(slot: int) -> None
recall_arb(slot: int) -> None
get_arb_execution_state() -> str
```

### 10.7 Battery Mode

Implement all `BATTery` charge/shutdown commands plus high-level guarded helpers:

```python
set_battery_charge_voltage(value: float | str) -> None
get_battery_charge_voltage(selector: str | None = None) -> float
set_battery_charge_current(value: float | str) -> None
get_battery_charge_current(selector: str | None = None) -> float
set_battery_shutdown_voltage(value: float | str) -> None
get_battery_shutdown_voltage(selector: str | None = None) -> float
set_battery_shutdown_current(value: float | str) -> None
get_battery_shutdown_current(selector: str | None = None) -> float
set_battery_shutdown_capacity(value: float | str) -> None
get_battery_shutdown_capacity(selector: str | None = None) -> float
set_battery_shutdown_time(value: float | str) -> None
get_battery_shutdown_time(selector: str | None = None) -> float
run_battery_mode() -> None
stop_battery_mode() -> None
set_battery_mode(mode: str) -> None  # e.g. CHAR if verified by hardware/manual example
```

### 10.8 Digital IO / Configurable IO

Implement wrappers for selecting IO, direction, reverse, PWM enable/frequency/duty, pulse width, IO type, trigger type/source, output level, and input level.

The catalog must keep the manual spelling `IO:TRIGer:SOURce`; an alias for `IO:TRIGger:SOURce` may be provided but must be hardware verified before use by default.

### 10.9 Status and Protection

Implement event, enable, positive transition, negative transition, condition, status preset, and decoded status helpers.

---

## 11. Exception Model

Use non-shadowing exception names:

```python
class ITM3900DError(Exception): ...
class VisaConnectionError(ITM3900DError): ...
class InstrumentError(ITM3900DError): ...
class InstrumentCommandError(InstrumentError): ...
class UnsupportedCommandError(InstrumentCommandError): ...
class OutputProtectionError(InstrumentError): ...
class QueryInterruptedError(InstrumentError): ...
class InstrumentTimeoutError(ITM3900DError): ...
class SafetyLimitError(ITM3900DError): ...
class OutputEnableNotAllowedError(SafetyLimitError): ...
```

Error queue behavior:

- `SYST:ERR?` reads one error from FIFO.
- Read until `+0` / `No error`, with a max-read guard.
- Overflow must be represented as an exception/warning record.
- `*CLS` and `SYST:CLE` shall be available.
- `*RST` must not be assumed to clear the error queue.

---

## 12. Tests and Acceptance Criteria

### 12.1 Unit Tests Without Hardware

- Command formatting for all catalog entries.
- Boolean conversion and discrete value validation.
- Query selector handling: `MINimum`, `MAXimum`, `DEFault`, `MIN`, `MAX`, `DEF`.
- Float formatting with engineering suffix strings preserved, e.g. `"5A"`, `"10KW"`.
- Error queue parsing.
- Query-interrupted error mapping.
- Socket/VXI-11 resource generation.
- Binary block parser.
- Dry-run logging.
- Safety policy refusal tests.
- No output-on commands during constructor, discovery, connect, reset, reconnect, or close unless explicitly configured.
- Output subsystem query commands are present in the catalog: `OUTPut:INHibit:MODE?`, `OUTPut:PON:STATe?`, `OUTPut:PROTection:WDOG[:STATe]?`, and `OUTPut:PROTection:WDOG:DELay?`.
- `FORMat[:data]?` is present in the catalog and has a wrapper.
- Guarded/dangerous command metadata is present and enforced for all commands listed in Section 6.3.

### 12.2 Hardware-in-Loop Smoke Tests

All HIL tests must require explicit user confirmation before output ON.

Minimum sequence:

```text
1. Connect over USB.
2. Query *IDN?.
3. Send SYST:REM.
4. Query SYST:VERS?.
5. Query MEAS:VOLT?, MEAS:CURR?, MEAS:POW?.
6. Set safe voltage/current/power limits while output remains OFF.
7. Turn output ON only after explicit confirmation.
8. Measure voltage/current/power.
9. Turn output OFF.
10. Verify measured voltage decays below configured safe threshold if verify_output_off=True.
11. Read and print full error queue.
12. Repeat over Ethernet VXI-11 and raw socket.
```

### 12.3 Production Acceptance Matrix

| Area | Required result |
|---|---|
| Type checking | `mypy` clean for package code |
| Linting | `ruff check` clean |
| Unit tests | `pytest` pass without hardware |
| Catalog coverage | 100% Appendix A + B represented |
| Mock transport | Full command/query behavior tested |
| Safety | Output cannot turn ON accidentally |
| USB HIL | IDN, remote, set, measure, output off verified |
| Ethernet VXI-11 HIL | Same as USB |
| Ethernet socket HIL | Same as USB |
| ELOG/DLOG | ASCII and binary behavior documented |
| ARB/list | At least one voltage list profile verified |
| Documentation | README includes safety warnings and verified connection strings |

---

## 13. README Examples Required

### 13.1 USB Safe Example

```python
from itm3900d import ITM3900D, SafetyPolicy

policy = SafetyPolicy(max_voltage_v=30.0, max_current_a=5.0, max_power_w=100.0)

with ITM3900D.open_usb(safety=policy, allow_output_enable=False) as psu:
    print(psu.idn())
    psu.set_remote()
    psu.configure_cv(voltage=12.0, current_limit=2.0, power_limit=50.0)
    print(psu.measure_voltage())
    psu.output_off()
```

### 13.2 Ethernet Socket Example

```python
from itm3900d import ITM3900D, SafetyPolicy

policy = SafetyPolicy(max_voltage_v=10.0, max_current_a=1.0, max_power_w=10.0)

psu = ITM3900D.open_ethernet(
    "192.168.0.50",
    lan_mode="socket",
    port=5025,
    safety=policy,
    allow_output_enable=False,
)
print(psu.idn())
psu.set_remote()
psu.configure_cv(voltage=5.0, current_limit=1.0, power_limit=5.0)
psu.output_off()
psu.close()
```

### 13.3 Explicit Output Enable Example

```python
from itm3900d import ITM3900D, SafetyPolicy

policy = SafetyPolicy(max_voltage_v=5.5, max_current_a=0.5, max_power_w=3.0)
psu = ITM3900D.open_usb(safety=policy, allow_output_enable=True)
psu.configure_cv(voltage=5.0, current_limit=0.2, power_limit=2.0)

answer = input("Type ENABLE to turn output ON: ")
if answer == "ENABLE":
    psu.output_on(confirm=True)

psu.output_off(verify=True)
psu.close()
```

---

## 14. Implementation Notes for Coding Agent

- Internally prefer exact long-form SCPI strings from the catalog.
- Examples may use common short forms only when readability improves.
- Do not invent electrical limits. Use user `SafetyPolicy` plus queried instrument limits where supported.
- Do not silently ignore SCPI errors in strict mode.
- Keep `strict=False` for high-speed scripts but document the risk.
- Add docstrings showing exact SCPI command and return type.
- Add `verified_on` metadata only after real hardware testing.
- Mark commands from the manual examples but not the formal command list as `manual_example_only` until hardware verified.
- Include notes that USB TMC and U-disk cannot be used at the same time when documenting DLOG behavior, matching the manual example note.
- The generated package may be marked "production-intent" after unit tests, but shall not be labelled "production verified" until HIL results are recorded for the exact firmware/interface combination.

---

## 15. Known Manual Ambiguities to Handle Explicitly

The implementation must not hide ambiguous areas. It should expose them in README and command metadata.

1. `BATT:MODE CHAR` appears in the manual examples but is not visible in the TOC-derived battery command list. Implement as a guarded compatibility helper and verify with `SYST:ERR?`.
2. `IO:TRIGer:SOURce` has a spelling with one `g` in the manual TOC. Use the manual spelling by default; provide a second alias only after hardware verification.
3. Some query forms are documented in command pages but missing from the TOC. Appendix B lists these supplemental queries.
4. Binary ELOG data framing must be verified on real hardware; retain raw bytes if decoding is uncertain.
5. Instrument LAN resource mode may differ by firmware/options; support VXI-11 and socket with configurable fallback.
6. `OUTPut:PON:STATe` values and recall behavior must be treated as safety-critical until verified on the target instrument.

---

## Appendix A - Baseline SCPI Command Catalog From Manual TOC

Baseline command count: **330**. This is not sufficient alone; also implement Appendix B.

### SYSTem Subsystem

- `SYSTem:POSetup <CPD>`
- `SYSTem:POSetup?`
- `SYSTem:VERSion?`
- `SYSTem:ERRor?`
- `SYSTem:CLEar`
- `SYSTem:REMote`
- `SYSTem:LOCal`
- `SYSTem:RWLock`
- `SYSTem:BEEPer:IMMediate`
- `SYSTem:BEEPer[:STATe] <CPD>`
- `SYSTem:BEEPer[:STATe]?`
- `SYSTem:DATE <yyyy>,<mm>,<dd>`
- `SYSTem:DATE?`
- `SYSTem:TIME <hh>,<mm>,<ss>`
- `SYSTem:TIME?`
- `SYSTem:COMMunicate:SELect <CPD>`
- `SYSTem:COMMunicate:SELect?`
- `SYSTem:COMMunicate:GPIB:ADDRess <NR1>`
- `SYSTem:COMMunicate:GPIB:ADDRess?`
- `SYSTem:COMMunicate:SERial:BAUDrate <CPD>`
- `SYSTem:COMMunicate:SERial:BAUDrate?`
- `SYSTem:COMMunicate:SERial:ADDRess <NR1>`
- `SYSTem:COMMunicate:LAN:IP[:CONFiguration] <SPD>`
- `SYSTem:COMMunicate:LAN:IP[:CONFiguration]?`
- `SYSTem:COMMunicate:LAN:IP[:CONFiguration]:MODE <CPD>`
- `SYSTem:COMMunicate:LAN:IP[:CONFiguration]:MODE?`
- `SYSTem:COMMunicate:LAN:SMASk <SPD>`
- `SYSTem:COMMunicate:LAN:SMASk?`
- `SYSTem:COMMunicate:LAN:DGATeway <SPD>`
- `SYSTem:COMMunicate:LAN:DGATeway?`
### [SOURce] Subsystem

- `[SOURce:]FUNCtion <CPD>`
- `[SOURce:]FUNCtion?`
- `[SOURce:]FUNCtion:MODE <CPD>`
- `[SOURce:]FUNCtion:MODE?`
- `[SOURce:]CURRent[:LEVel][:IMMediate][:AMPLitude] <NRf+>`
- `[SOURce:]CURRent[:LEVel][:IMMediate][:AMPLitude]? [MINimum|MAXimum|DEFault]`
- `[SOURce:]CURRent:SLEW[:BOTH] <NRf+>`
- `[SOURce:]CURRent:SLEW[:BOTH]? [MINimum|MAXimum|DEFault]`
- `[SOURce:]CURRent:SLEW:POSitive <NRf+>`
- `[SOURce:]CURRent:SLEW:POSitive? [MINimum|MAXimum|DEFault]`
- `[SOURce:]CURRent:SLEW:NEGative <NRf+>`
- `[SOURce:]CURRent:SLEW:NEGative? [MINimum|MAXimum|DEFault]`
- `[SOURce:]CURRent[:OVER]:PROTection:STATe <Bool>`
- `[SOURce:]CURRent[:OVER]:PROTection:STATe?`
- `[SOURce:]CURRent[:OVER]:PROTection[:LEVel] <NRf+>`
- `[SOURce:]CURRent[:OVER]:PROTection[:LEVel]?`
- `[SOURce:]CURRent[:OVER]:PROTection:DELay[:TIME] <NRf+>`
- `[SOURce:]CURRent[:OVER]:PROTection:DELay[:TIME]? [MINimum|MAXimum|DEFault]`
- `[SOURce:]CURRent:UNDer:PROTection:STATe <Bool>`
- `[SOURce:]CURRent:UNDer:PROTection:STATe?`
- `[SOURce:]CURRent:UNDer:PROTection[:LEVel] <NRf+>`
- `[SOURce:]CURRent:UNDer:PROTection[:LEVel]?`
- `[SOURce:]CURRent:UNDer:PROTection:DELay[:TIME] <NRf+>`
- `[SOURce:]CURRent:UNDer:PROTection:DELay[:TIME]? [MINimum|MAXimum|DEFault]`
- `[SOURce:]CURRent:UNDer:PROTection:WARM[:TIME] <NRf+>`
- `[SOURce:]CURRent:UNDer:PROTection:WARM[:TIME]? [MINimum|MAXimum|DEFault]`
- `[SOURce:]CURRent:LIMit[:POSitive][:IMMediate][:AMPLitude] <NRf+>`
- `[SOURce:]CURRent:LIMit[:POSitive][:IMMediate][:AMPLitude]? [MINimum|MAXimum|DEFault]`
- `[SOURce:]VOLTage[:LEVel][:IMMediate][:AMPLitude] <NRf+>`
- `[SOURce:]VOLTage[:LEVel][:IMMediate][:AMPLitude]? [MINimum|MAXimum|DEFault]`
- `[SOURce:]VOLTage:SLEW[:BOTH] <NRf+>`
- `[SOURce:]VOLTage:SLEW[:BOTH]? [MINimum|MAXimum|DEFault]`
- `[SOURce:]VOLTage:SLEW:POSitive <NRf+>`
- `[SOURce:]VOLTage:SLEW:POSitive? [MINimum|MAXimum|DEFault]`
- `[SOURce:]VOLTage:SLEW:NEGative <NRf+>`
- `[SOURce:]VOLTage:SLEW:NEGative? [MINimum|MAXimum|DEFault]`
- `[SOURce:]VOLTage[:OVER]:PROTection:STATe <Bool>`
- `[SOURce:]VOLTage[:OVER]:PROTection:STATe?`
- `[SOURce:]VOLTage[:OVER]:PROTection[:LEVel] <NRf+>`
- `[SOURce:]VOLTage[:OVER]:PROTection[:LEVel]?`
- `[SOURce:]VOLTage[:OVER]:PROTection:DELay[:TIME] <NRf+>`
- `[SOURce:]VOLTage[:OVER]:PROTection:DELay[:TIME]? [MINimum|MAXimum|DEFault]`
- `[SOURce:]VOLTage:UNDer:PROTection:STATe <Bool>`
- `[SOURce:]VOLTage:UNDer:PROTection:STATe?`
- `[SOURce:]VOLTage:UNDer:PROTection[:LEVel] <NRf+>`
- `[SOURce:]VOLTage:UNDer:PROTection[:LEVel]?`
- `[SOURce:]VOLTage:UNDer:PROTection:DELay[:TIME] <NRf+>`
- `[SOURce:]VOLTage:UNDer:PROTection:DELay[:TIME]? [MINimum|MAXimum|DEFault]`
- `[SOURce:]VOLTage:UNDer:PROTection:WARM[:TIME] <NRf+>`
- `[SOURce:]VOLTage:UNDer:PROTection:WARM[:TIME]? [MINimum|MAXimum|DEFault]`
- `[SOURce:]VOLTage:LIMit[:POSitive][:IMMediate][:AMPLitude] <NRf+>`
- `[SOURce:]VOLTage:LIMit[:POSitive][:IMMediate][:AMPLitude]? [MINimum|MAXimum|DEFault]`
- `[SOURce:]POWer:LIMit[:POSitive][:IMMediate][:AMPLitude] <NRf+>`
- `[SOURce:]POWer:LIMit[:POSitive][:IMMediate][:AMPLitude]? [MINimum|MAXimum|DEFault]`
- `[SOURce:]POWer[:OVER]:PROTection:STATe <Bool>`
- `[SOURce:]POWer[:OVER]:PROTection:STATe?`
- `[SOURce:]POWer[:OVER]:PROTection[:LEVel] <NRf+>`
- `[SOURce:]POWer[:OVER]:PROTection[:LEVel]?`
- `[SOURce:]POWer[:OVER]:PROTection:DELay[:TIME] <NRf+>`
- `[SOURce:]POWer[:OVER]:PROTection:DELay[:TIME]? [MINimum|MAXimum|DEFault]`
- `[SOURce:]RESistance[:LEVel][:IMMediate][:AMPLitude] <NRf+>`
- `[SOURce:]RESistance[:LEVel][:IMMediate][:AMPLitude]? [MINimum|MAXimum|DEFault]`
- `[SOURce:]EXTern:PROGram[:STATe] <Bool>`
- `[SOURce:]EXTern:PROGram[:STATe]?`
- `[SOURce:]EXTern:PROGram:CHANnel:MX <NR1>,<NRf>`
- `[SOURce:]EXTern:PROGram:CHANnel:MX? <NR1>`
- `[SOURce:]EXTern:PROGram:CHANnel:MB <NR1>,<NRf>`
- `[SOURce:]EXTern:PROGram:CHANnel:MB? <NR1>`
- `[SOURce:]FILTer:LEVel <CPD>`
- `[SOURce:]FILTer:LEVel?`
- `[SOURce:]CV:PRIority <priority>`
- `[SOURce:]CC:PRIority <priority>`
### OUTPut Subsystem

- `OUTPut[:STATe] <CPD>`
- `OUTPut[:STATe]?`
- `OUTPut:DELay:FALL <NRf+>`
- `OUTPut:DELay:FALL? [MINimum|MAXimum|DEFault]`
- `OUTPut:DELay:RISE <NRf+>`
- `OUTPut:DELay:RISE? [MINimum|MAXimum|DEFault]`
- `OUTPut:INHibit:MODE <CPD>`
- `OUTPut:PON:STATe <CPD>`
- `OUTPut:PROTection:CLEar`
- `OUTPut:PROTection:WDOG[:STATe] <CPD>`
- `OUTPut:PROTection:WDOG:DELay <NRf+>`
### ABORt Subsystem

- `ABORt:ACQuire`
- `ABORt:ARB`
### INITiate Subsystem

- `INITiate[:IMMediate]:ACQuire`
- `INITiate[:IMMediate]:ARB`
- `INITiate:CONTinuous:ARB <Bool>`
- `INITiate:CONTinuous:ACQuire <Bool>`
- `INITiate[:IMMediate]:DLOG`
- `INITiate[:IMMediate]:ELOG`
### BATTery Subsystem

- `BATTery:CHARge:VOLTage <NRf+>`
- `BATTery:CHARge:VOLTage? [MINimum|MAXimum|DEFault]`
- `BATTery:CHARge:CURRent <NRf+>`
- `BATTery:CHARge:CURRent? [MINimum|MAXimum|DEFault]`
- `BATTery:SHUT:VOLTage <NRf+>`
- `BATTery:SHUT:VOLTage? [MINimum|MAXimum|DEFault]`
- `BATTery:SHUT:CURRent <NRf+>`
- `BATTery:SHUT:CURRent? [MINimum|MAXimum|DEFault]`
- `BATTery:SHUT:CAPacity <NRf+>`
- `BATTery:SHUT:CAPacity? [MINimum|MAXimum|DEFault]`
- `BATTery:SHUT:TIME <NRf+>`
- `BATTery:SHUT:TIME? [MINimum|MAXimum|DEFault]`

### CONFigurable IO Subsystem

- `IO:SELect <NR1>`
- `IO:SELect?`
- `IO:DIREction <NRL>, <Bool>`
- `IO:DIREction? <NRL>`
- `IO:REVErse <NRL>, <Bool>`
- `IO:REVErse? <NRL>`
- `IO:PWM[:ENABle] <NRL>, <Bool>`
- `IO:PWM[:ENABle]? <NRL>`
- `IO:PWM:FREQuency <NRL>, <NRf+>`
- `IO:PWM:FREQuency? <NRL>[, ][MINimum|MAXimum|DEFault]`
- `IO:PWM:DUTY <NRL>, <NR1>`
- `IO:PWM:DUTY? <NRL>`
- `IO:PULSe:WIDTh <NRL>, <NRf+>`
- `IO:PULSe:WIDTh? <NRL>[, ][MINimum|MAXimum|DEFault]`
- `IO:TYPE <NRL>, <CPD>`
- `IO:TYPE? <NRL>`
- `IO:TRIGger:TYPE <CPD>`
- `IO:TRIGger:TYPE?`
- `IO:TRIGer:SOURce <CPD>`
- `IO:TRIGer:SOURce?`
- `IO:OUTPut:LEVel <NRL>, <CPD>`
- `IO:OUTPut:LEVel? <NRL>`
- `IO:INPut:LEVel? <NRL>`
### TRIGger Subsystem

- `TRIGger:ACQuire[:IMMediate]`
- `TRIGger:ACQuire:MODE <CPD>`
- `TRIGger:ACQuire:SOURce <CPD>`
- `TRIGger:ACQuire:VOLTage:SLOPe <CPD>`
- `TRIGger:ACQuire:VOLTage[:LEVel] <NRf+>`
- `TRIGger:ACQuire:VOLTage:HYSTeresis:HIGH <NRf+>`
- `TRIGger:ACQuire:VOLTage:HYSTeresis:LOW <NRf+>`
- `TRIGger:ACQuire:CURRent:SLOPe <CPD>`
- `TRIGger:ACQuire:CURRent[:LEVel] <NRf+>`
- `TRIGger:ACQuire:CURRent:HYSTeresis:HIGH <NRf+>`
- `TRIGger:ACQuire:CURRent:HYSTeresis:LOW <NRf+>`
- `TRIGger:ARB[:IMMediate]`
- `TRIGger:ARB:SOURce <CPD>`
- `TRIGger:DLOG:SOURce <CPD>`
- `TRIGger:DLOG[:IMMediate]`
- `TRIGger:DLOG:CURRent:SLOPe <CPD>`
- `TRIGger:DLOG:CURRent[:LEVel] <NRf+>`
- `TRIGger:DLOG:CURRent:HYSTeresis:HIGH <NRf+>`
- `TRIGger:DLOG:CURRent:HYSTeresis:LOW <NRf+>`
- `TRIGger:DLOG:VOLTage:SLOPe <CPD>`
- `TRIGger:DLOG:VOLTage[:LEVel] <NRf+>`
- `TRIGger:DLOG:VOLTage:HYSTeresis:HIGH <NRf+>`
- `TRIGger:DLOG:VOLTage:HYSTeresis:LOW <NRf+>`
- `TRIGger:ELOG:SOURce <CPD>`
- `TRIGger:ELOG[:IMMediate]`
- `TRIGger:ELOG:CURRent:SLOPe <CPD>`
- `TRIGger:ELOG:CURRent[:LEVel] <NRf+>`
- `TRIGger:ELOG:CURRent:HYSTeresis:HIGH <NRf+>`
- `TRIGger:ELOG:CURRent:HYSTeresis:LOW <NRf+>`
- `TRIGger:ELOG:VOLTage:SLOPe <CPD>`
- `TRIGger:ELOG:VOLTage[:LEVel] <NRf+>`
- `TRIGger:ELOG:VOLTage:HYSTeresis:HIGH <NRf+>`
- `TRIGger:ELOG:VOLTage:HYSTeresis:LOW <NRf+>`
### STATus Subsystem

- `STATus:QUEStionable[:EVENt]?`
- `STATus:QUEStionable:ENABle <NR1>`
- `STATus:QUEStionable:PTRansition <NR1>`
- `STATus:QUEStionable:NTRansition <NR1>`
- `STATus:QUEStionable:CONDition?`
- `STATus:OPERation[:EVENt]?`
- `STATus:OPERation:ENABle <NR1>`
- `STATus:OPERation:PTRansition <NR1>`
- `STATus:OPERation:NTRansition <NR1>`
- `STATus:OPERation:CONDition?`
- `STATus:PRESet`
### FETCh Subsystem

- `FETCh[:SCALar]:CURRent[:DC]?`
- `FETCh[:SCALar]:CURRent[:DC]:HIGH?`
- `FETCh[:SCALar]:CURRent[:DC]:LOW?`
- `FETCh[:SCALar]:CURRent[:DC]:MAXimum?`
- `FETCh[:SCALar]:CURRent[:DC]:MINimum?`
- `FETCh[:SCALar]:VOLTage[:DC]?`
- `FETCh[:SCALar]:VOLTage[:DC]:HIGH?`
- `FETCh[:SCALar]:VOLTage[:DC]:LOW?`
- `FETCh[:SCALar]:VOLTage[:DC]:MAXimum?`
- `FETCh[:SCALar]:VOLTage[:DC]:MINimum?`
- `FETCh[:SCALar]:POWer[:DC]?`
- `FETCh[:SCALar]:POWer[:DC]:MAXimum?`
- `FETCh[:SCALar]:POWer[:DC]:MINimum?`
- `FETCh:ARRay:CURRent[:DC]?`
- `FETCh:ARRay:VOLTage[:DC]?`
- `FETCh:ARRay:POWer[:DC]?`
- `FETCh[:SCALar]?`
- `ELOG:STATe?`
- `DLOG:STATe?`
- `FETCh:ELOG:ARRay:DATA[:DC]?`
### MEASure Subsystem

- `MEASure[:SCALar]:CURRent[:DC]?`
- `MEASure[:SCALar]:CURRent:HIGH?`
- `MEASure[:SCALar]:CURRent:LOW?`
- `MEASure[:SCALar]:CURRent:MAXimum?`
- `MEASure[:SCALar]:CURRent:MINimum?`
- `MEASure[:SCALar]:VOLTage[:DC]?`
- `MEASure[:SCALar]:VOLTage:HIGH?`
- `MEASure[:SCALar]:VOLTage:LOW?`
- `MEASure[:SCALar]:VOLTage:MAXimum?`
- `MEASure[:SCALar]:VOLTage:MINimum?`
- `MEASure[:SCALar]:POWer[:DC]?`
- `MEASure[:SCALar]:POWer:MAXimum?`
- `MEASure[:SCALar]:POWer:MINimum?`
- `MEASure:ARRay:CURRent[:DC]?`
- `MEASure:ARRay:VOLTage[:DC]?`
- `MEASure:ARRay:POWer[:DC]?`
- `MEASure[:SCALar]?`
### PARallel Subsystem

- `PARallel:ROLE <CPD>`
- `PARallel:NUMBer <NR1>`
### SENSe Subsystem

- `[SOURce:]REMote:SENSe[:STATe] <Bool>`
- `SENSe:ACQuire:POINts <NRf+>`
- `SENSe:ACQuire:OFFSet:POINt <NRf+>`
- `SENSe:ACQuire:TINTerval <NRf+>`
- `SENSe:ELOG:FUNCtion:CURRent <Bool>`
- `SENSe:ELOG:FUNCtion:VOLTage <Bool>`
- `SENSe:ELOG:FUNCtion:PEAK <Bool>`
- `SENSe:ELOG:PERiod <NRf+>`
- `SENSe:ELOG:TIME <NRf+>`
- `SENSe:DLOG:FUNCtion:CURRent <Bool>`
- `SENSe:DLOG:FUNCtion:VOLTage <Bool>`
- `SENSe:DLOG:FUNCtion:PEAK <Bool>`
- `SENSe:DLOG:PERiod <NRf+>`
- `SENSe:DLOG:TIME <NRf+>`
### ARB Subsystem

- `ARB:COUNt <NRf+>`
- `ARB:TERMinate:LAST <CPD>`
- `ARB:FUNCtion:TYPE <CPD>`
- `ARB:FUNCtion:SHAPe <CPD>`
- `ARB:PULSe:STARt[:LEVel] <NRf+>`
- `ARB:PULSe:STARt:TIME <NRf+>`
- `ARB:PULSe:STARt:SLEW <NRf+>`
- `ARB:PULSe:TOP[:LEVel] <NRf+>`
- `ARB:PULSe:TOP:TIME <NRf+>`
- `ARB:PULSe:END:TIME <NRf+>`
- `ARB:PULSe:END:SLEW <NRf+>`
- `ARB:SINusoid:AMPLitude <NRf+>`
- `ARB:SINusoid:OFFSet <NRf+>`
- `ARB:SINusoid:FREQuency <NRf+>`
- `ARB:SWEep:AMPLitude <NRf+>`
- `ARB:SWEep:OFFSet <NRf+>`
- `ARB:SWEep:STARt <NRf+>`
- `ARB:SWEep:END <NRf+>`
- `ARB:SWEep:STEP[:LEVel] <NRf+>`
- `ARB:SWEep:STEP:WIDTh <NRf+>`
- `ARB:UDEFined:COUNt <NR1>`
- `ARB:UDEFined:LEVel <NR1>,<NRf+>`
- `ARB:UDEFined:DWELl <NR1>,<NRf+>`
- `ARB:UDEFined:SLEW <NR1>,<NRf+>`
- `ARB:UDEFined:TRIgout <CPD>`
- `ARB:CDWell:POINts <NR1>`
- `ARB:CDWell[:LEVel] <NRf+>,<NRf+>,<NR1>`
- `ARB:CDWell:DWELl <NRf+>`
- `ARB:CDWell:STOP`
- `ARB:SEQuence:LENGth <NR1>`
- `ARB:SEQuence:SELect <NR1>`
- `ARB:SEQuence:COUNt <NR1>`
- `ARB:SEQuence:FUNCtion <CPD>`
- `ARB:SEQuence:PACing <CPD>`
- `ARB:SEQuence:PULSe:STARt[:LEVel] <NRf+>`
- `ARB:SEQuence:PULSe:STARt:TIME <NRf+>`
- `ARB:SEQuence:PULSe:STARt:SLEW <NRf+>`
- `ARB:SEQuence:PULSe:TOP:LEVel <NRf+>`
- `ARB:SEQuence:PULSe:TOP:TIME <NRf+>`
- `ARB:SEQuence:PULSe:END:TIME <NRf+>`
- `ARB:SEQuence:PULSe:END:SLEW <NRf+>`
- `ARB:SEQuence:PULSe:REPeate <NRf+>`
- `ARB:SEQuence:SINusoid:AMPLitude <NRf+>`
- `ARB:SEQuence:SINusoid:OFFSet <NRf+>`
- `ARB:SEQuence:SINusoid:FREQuency <NRf+>`
- `ARB:SEQuence:UDEFined:LEVel <NR1>,<NRf+>`
- `ARB:SEQuence:UDEFined:DWELl <NR1>,<NRf+>`
- `ARB:SEQuence:UDEFined:SLEW <NR1>,<NRf+>`
- `ARB:SAVE <NR1>`
- `ARB:RECall <NR1>`
- `ARB:EXE:STATe?`
- `ARB:SEQuence:CDWell:POINts <NR1>`
- `ARB:SEQuence:CDWell:LEVel <NRf+>,<NRf+>,<NR1>`
- `ARB:SEQuence:CDWell:WIDth <NRf+>`
- `ARB:ZOOM:COF <NRf>`
- `ARB:ZOOM:LIMIt:POSitive <NR1>`
- `ARB:ZOOM:LIMIt:NEGative <NR1>`
- `ARB:PAUSe:STATe <Bool>`

### IEEE-488 Common Commands

- `*CLS`
- `*ESE <NR1>`
- `*ESE?`
- `*ESR?`
- `*IDN?`
- `*OPC`
- `*OPC?`
- `*RST`
- `*SRE <NR1>`
- `*SRE?`
- `*STB?`
- `*TRG`
- `*SAV <NR1>`
- `*RCL <NR1>`
- `*TST?`
- `*WAI`
- `*PSC <Bool>`
- `*PSC?`

### FORMat Subsystem

- `FORMat[:data] <CPD>`

---

## Appendix B - Supplemental Query Syntax From Command Pages

These entries were found from command-page `Syntax` / `Query Syntax` sections and are required in addition to Appendix A when not already duplicated by the TOC list. Page numbers refer to the programming guide page numbers, not PDF viewer indices.

Supplemental command/query count is advisory only. The generated `test_catalog_coverage.py` and `command_catalog.py` coverage check are the authority for completeness.

### SYSTem

- Page 44: `SYSTem:COMMunicate:SERial:ADDRess?`


### OUTPut supplemental safety queries

- Page 113: `OUTPut:INHibit:MODE?`
- Page 114: `OUTPut:PON:STATe?`
- Page 116: `OUTPut:PROTection:WDOG[:STATe]?`
- Page 117: `OUTPut:PROTection:WDOG:DELay? [MINimum|MAXimum|DEFault]`

### SOURce / optional-source supplemental queries

- Page 107: `[SOURce:]CV:PRIority?`
- Page 108: `[SOURce:]CC:PRIority?`
- Page 231: `[SOURce:]REMote:SENSe[:STATe]?`

### TRIGger

- Page 157: `TRIGger:ACQuire:MODE?`
- Page 158: `TRIGger:ACQuire:SOURce?`
- Page 159: `TRIGger:ACQuire:VOLTage:SLOPe?`
- Page 160: `TRIGger:ACQuire:VOLTage[:LEVel]? [MIN|MAX|DEF]`
- Page 161: `TRIGger:ACQuire:VOLTage:HYSTeresis:HIGH? [MIN|MAX|DEF]`
- Page 162: `TRIGger:ACQuire:VOLTage:HYSTeresis:LOW? [MIN|MAX|DEF]`
- Page 163: `TRIGger:ACQuire:CURRent:SLOPe?`
- Page 164: `TRIGger:ACQuire:CURRent[:LEVel]? [MIN|MAX|DEF]`
- Page 165: `TRIGger:ACQuire:CURRent:HYSTeresis:HIGH? [MIN|MAX|DEF]`
- Page 166: `TRIGger:ACQuire:CURRent:HYSTeresis:LOW? [MIN|MAX|DEF]`
- Page 167: `TRIGger:ARB:SOURce?`
- Page 169: `TRIGger:DLOG:SOURce?`
- Page 170: `TRIGger:DLOG:CURRent:SLOPe?`
- Page 171: `TRIGger:DLOG:CURRent[:LEVel]? [MIN|MAX|DEF]`
- Page 172: `TRIGger:DLOG:CURRent:HYSTeresis:HIGH? [MIN|MAX|DEF]`
- Page 173: `TRIGger:DLOG:CURRent:HYSTeresis:LOW? [MIN|MAX|DEF]`
- Page 174: `TRIGger:DLOG:VOLTage:SLOPe?`
- Page 175: `TRIGger:DLOG:VOLTage[:LEVel]? [MIN|MAX|DEF]`
- Page 175: `TRIGger:DLOG:VOLTage:HYSTeresis:HIGH? [MIN|MAX|DEF]`
- Page 176: `TRIGger:DLOG:VOLTage:HYSTeresis:LOW? [MIN|MAX|DEF]`
- Page 177: `TRIGger:ELOG:SOURce?`
- Page 179: `TRIGger:ELOG:CURRent:SLOPe?`
- Page 180: `TRIGger:ELOG:CURRent[:LEVel]? [MIN|MAX|DEF]`
- Page 181: `TRIGger:ELOG:CURRent:HYSTeresis:HIGH? [MIN|MAX|DEF]`
- Page 182: `TRIGger:ELOG:CURRent:HYSTeresis:LOW? [MIN|MAX|DEF]`
- Page 183: `TRIGger:ELOG:VOLTage:SLOPe?`
- Page 183: `TRIGger:ELOG:VOLTage[:LEVel]? [MIN|MAX|DEF]`
- Page 184: `TRIGger:ELOG:VOLTage:HYSTeresis:HIGH? [MIN|MAX|DEF]`
- Page 185: `TRIGger:ELOG:VOLTage:HYSTeresis:LOW? [MIN|MAX|DEF]`

### STATus

- Page 191: `STATus:QUEStionable:ENABle?`
- Page 192: `STATus:QUEStionable:PTRansition?`
- Page 193: `STATus:QUEStionable:NTRansition?`
- Page 196: `STATus:OPERation:ENABle?`
- Page 197: `STATus:OPERation:PTRansition?`
- Page 198: `STATus:OPERation:NTRansition?`

### PARallel

- Page 229: `PARallel:ROLE?`
- Page 230: `PARallel:NUMBer?`

### SENSe

- Page 232: `SENSe:ACQuire:POINts? [MIN|MAX|DEF]`
- Page 233: `SENSe:ACQuire:OFFSet:POINt? [MIN|MAX|DEF]`
- Page 234: `SENSe:ACQuire:TINTerval? [MIN|MAX|DEF]`
- Page 234: `SENSe:ELOG:FUNCtion:CURRent?`
- Page 235: `SENSe:ELOG:FUNCtion:VOLTage?`
- Page 236: `SENSe:ELOG:FUNCtion:PEAK?`
- Page 237: `SENSe:ELOG:PERiod? [MIN|MAX|DEF]`
- Page 238: `SENSe:ELOG:TIME? [MIN|MAX|DEF]`
- Page 238: `SENSe:DLOG:FUNCtion:CURRent?`
- Page 239: `SENSe:DLOG:FUNCtion:VOLTage?`
- Page 240: `SENSe:DLOG:FUNCtion:PEAK?`
- Page 241: `SENSe:DLOG:PERiod? [MIN|MAX|DEF]`
- Page 242: `SENSe:DLOG:TIME? [MIN|MAX|DEF]`

### ARB

- Page 243: `ARB:COUNt? [MIN|MAX]`
- Page 244: `ARB:TERMinate:LAST?`
- Page 245: `ARB:FUNCtion:TYPE?`
- Page 246: `ARB:FUNCtion:SHAPe?`
- Page 247: `ARB:PULSe:STARt[:LEVel]? [MIN|MAX|DEF]`
- Page 248: `ARB:PULSe:STARt:TIME? [MIN|MAX|DEF]`
- Page 249: `ARB:PULSe:STARt:SLEW? [MIN|MAX|DEF]`
- Page 249: `ARB:PULSe:TOP[:LEVel]? [MIN|MAX|DEF]`
- Page 250: `ARB:PULSe:TOP:TIME? [MIN|MAX|DEF]`
- Page 251: `ARB:PULSe:END:TIME? [MIN|MAX|DEF]`
- Page 252: `ARB:PULSe:END:SLEW? [MIN|MAX|DEF]`
- Page 253: `ARB:SINusoid:AMPLitude? [MIN|MAX|DEF]`
- Page 253: `ARB:SINusoid:OFFSet? [MIN|MAX|DEF]`
- Page 254: `ARB:SINusoid:FREQuency? [MIN|MAX|DEF]`
- Page 255: `ARB:SWEep:AMPLitude? [MIN|MAX|DEF]`
- Page 256: `ARB:SWEep:OFFSet? [MIN|MAX|DEF]`
- Page 257: `ARB:SWEep:STARt? [MIN|MAX|DEF]`
- Page 257: `ARB:SWEep:END? [MIN|MAX|DEF]`
- Page 258: `ARB:SWEep:STEP[:LEVel]? [MIN|MAX|DEF]`
- Page 259: `ARB:SWEep:STEP:WIDTh? [MIN|MAX|DEF]`
- Page 260: `ARB:UDEFined:COUNt?`
- Page 261: `ARB:UDEFined:LEVel? <NR1>`
- Page 262: `ARB:UDEFined:DWELl? <NR1>`
- Page 263: `ARB:UDEFined:SLEW? <NR1>`
- Page 263: `ARB:UDEFined:TRIgout?`
- Page 264: `ARB:CDWell:POINts?`
- Page 265: `ARB:CDWell[:LEVel]? <NR1>`
- Page 266: `ARB:CDWell:DWELl? [MIN|MAX|DEF]`
- Page 268: `ARB:SEQuence:LENGth?`
- Page 269: `ARB:SEQuence:SELect?`
- Page 269: `ARB:SEQuence:COUNt?`
- Page 270: `ARB:SEQuence:FUNCtion?`
- Page 271: `ARB:SEQuence:PACing?`
- Page 272: `ARB:SEQuence:PULSe:STARt[:LEVel]? [MIN|MAX|DEF]`
- Page 273: `ARB:SEQuence:PULSe:STARt:TIME? [MIN|MAX|DEF]`
- Page 274: `ARB:SEQuence:PULSe:STARt:SLEW? [MIN|MAX|DEF]`
- Page 275: `ARB:SEQuence:PULSe:TOP:LEVel? [MIN|MAX|DEF]`
- Page 276: `ARB:SEQuence:PULSe:TOP:TIME? [MIN|MAX|DEF]`
- Page 276: `ARB:SEQuence:PULSe:END:TIME? [MIN|MAX|DEF]`
- Page 277: `ARB:SEQuence:PULSe:END:SLEW? [MIN|MAX|DEF]`
- Page 278: `ARB:SEQuence:PULSe:REPeate?`
- Page 279: `ARB:SEQuence:SINusoid:AMPLitude? [MIN|MAX|DEF]`
- Page 280: `ARB:SEQuence:SINusoid:OFFSet? [MIN|MAX|DEF]`
- Page 280: `ARB:SEQuence:SINusoid:FREQuency? [MIN|MAX|DEF]`
- Page 281: `ARB:SEQuence:UDEFined:LEVel? <NR1>`
- Page 282: `ARB:SEQuence:UDEFined:DWELl? <NR1>`
- Page 283: `ARB:SEQuence:UDEFined:SLEW? <NR1>`
- Page 286: `ARB:SEQuence:CDWell:POINts?`
- Page 287: `ARB:SEQuence:CDWell:LEVel? <NR1>`
- Page 288: `ARB:SEQuence:CDWell:WIDth? [MIN|MAX|DEF]`
- Page 290: `ARB:ZOOM:COF?`
- Page 291: `ARB:ZOOM:LIMIt:POSitive?`
- Page 291: `ARB:ZOOM:LIMIt:NEGative?`
- Page 292: `ARB:PAUSe:STATe?`


---

## Appendix C - Change History

### v1.3 final production-code-generation cleanup patch

- Moved `FORMat[:data]?` into Appendix B under a dedicated `FORMat` heading.
- Removed the misplaced Appendix C `FORMat` command section.
- Added missing Appendix A headings for configurable IO, IEEE-488 common commands, and FORMat.
- Strengthened `output_on(confirm=False)` so it must raise before sending any real output-enable command unless in dry-run or an explicitly unsafe test override.
- Added `test_output_on_confirmation_required.py`.
- Replaced the supplemental query count with an advisory note that catalog coverage tests are authoritative.

### v1.2 production-code-generation patch

- Fixed newline terminator examples.
- Added guarded/dangerous command metadata.
- Added missing output subsystem safety queries and catalog tests.
- Added `FORMat[:data]?` catalog requirement.
- Removed duplicate/artifact supplemental entries.

### v1.1 production update

- Added production-grade definition and acceptance gates.
- Added `SafetyPolicy` with explicit output enable permission and voltage/current/power clamps.
- Added transport locking, query serialization, logging, dry-run, and recovery requirements.
- Renamed custom timeout exception to `InstrumentTimeoutError` to avoid shadowing Python built-in `TimeoutError`.
- Added machine-readable `ScpiCommand` catalog metadata requirements.
- Added supplemental query catalog from command-page syntax sections.
- Added hardware-in-loop verification matrix for USB, VXI-11 Ethernet, raw socket Ethernet, ELOG/DLOG, and ARB/list.
- Added manual ambiguity handling for `BATT:MODE CHAR`, `IO:TRIGer:SOURce`, and binary ELOG format.


