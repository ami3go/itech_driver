"""Supervised output operations. Never equate programmed OFF with safe voltage.

No implicit reset, clear, retry, reconnect or protection disable. The caller
must independently qualify the bench and supply its own measurement limits.
This helper does not replace hardware interlocks or an emergency disconnect.
"""
from dataclasses import dataclass
import math
from scpi_driver_core import ConfigurationError, SafetyGuardError, ScpiDriverError
from scpi_driver_core.scpi.parsers import parse_bool, parse_float, parse_int


@dataclass(frozen=True)
class OutputEvidence:
    requested: bool | None
    programmed: bool | None
    questionable: int | None
    voltage_v: float | None
    current_a: float | None
    outcome: str
    error: str | None = None


def _finite(value):
    return type(value) in (int,float) and math.isfinite(value)


_OBSERVATION_METHODS = (
    "OutputSubsystem.state_query", "StatusSubsystem.ques_condition_query",
    "MeasurementSubsystem.voltage_query", "MeasurementSubsystem.current_query",
)
_ON_METHODS = _OBSERVATION_METHODS + (
    "OutputSubsystem.state_set",
    "SourceSubsystem.ovp_enable_query", "SourceSubsystem.ovp_query",
    "SourceSubsystem.ocp_enable_query", "SourceSubsystem.ocp_query",
    "SourceSubsystem.opp_enable_query", "SourceSubsystem.opp_threshold_query",
    "SourceSubsystem.voltage_limit_query", "SourceSubsystem.current_limit_query",
    "SourceSubsystem.programmed_power_limit_query", "SourceSubsystem.voltage_query",
    "SourceSubsystem.current_query", "SourceSubsystem.function_mode_query",
    "SourceSubsystem.external_programming_query",
)


def observe_output(driver, *, requested=None):
    """Read separate evidence; no physical safe-state assertion."""
    programmed = questionable = voltage = current = None
    try:
        with driver.session.operation_lock():
            driver._require_methods(*_OBSERVATION_METHODS)
            programmed = driver.output.state_query()
            questionable = driver.status.ques_condition_query()
            if not 0 <= questionable <= 65535:
                raise ConfigurationError("invalid questionable register")
            voltage = driver.measurement.voltage_query()
            current = driver.measurement.current_query()
        return OutputEvidence(requested,programmed,questionable,voltage,current,"observed")
    except ScpiDriverError as exc:
        return OutputEvidence(requested,programmed,questionable,voltage,current,"unknown",str(exc))


def request_output_on(driver, *, authorized=False, max_voltage_v, max_current_a, max_power_w):
    """One explicit ON request after conservative read-only preflight.

    Caller authorization is not hardware qualification. Any failed write or
    verification yields unknown; the caller must use an independent safety path.
    """
    if authorized is not True:
        raise SafetyGuardError("explicit operator authorization required")
    bounds = (max_voltage_v,max_current_a,max_power_w)
    if any(not _finite(v) or v <= 0 for v in bounds):
        raise ConfigurationError("finite positive caller limits required")
    with driver.session.operation_lock():
        driver._require_methods(*_ON_METHODS)
        before = observe_output(driver)
        if before.outcome != "observed" or before.programmed is not False or before.questionable != 0:
            raise SafetyGuardError("output preflight not clear")
        source = driver.source
        checks = (("VOLT", source.ovp_enable_query, source.ovp_query, source.voltage_limit_query),
                  ("CURR", source.ocp_enable_query, source.ocp_query, source.current_limit_query),
                  ("POW", source.opp_enable_query, source.opp_threshold_query, source.programmed_power_limit_query))
        for (quantity, enabled_query, threshold_query, limit_query), ceiling in zip(checks,bounds):
            enabled = enabled_query()
            threshold = threshold_query()
            limit = limit_query()
            if not enabled or not 0 < threshold <= ceiling or not 0 < limit <= ceiling:
                raise SafetyGuardError(f"{quantity} protection/limit not inside caller envelope")
        for (quantity, query), ceiling in zip((("VOLT", source.voltage_query), ("CURR", source.current_query)),bounds):
            value = query()
            if not 0 <= value <= ceiling:
                raise SafetyGuardError(f"{quantity} setpoint outside caller envelope")
        if source.function_mode_query() not in ("FIX","FIXED"):
            raise SafetyGuardError("supervised enable supports fixed mode only")
        if source.external_programming_query():
            raise SafetyGuardError("external analog control not disabled")
        try:
            driver.output.state_set(True)
        except ScpiDriverError as exc:
            return OutputEvidence(True,None,None,None,None,"unknown",str(exc))
        observed = observe_output(driver,requested=True)
        if observed.programmed is not True or observed.questionable != 0 or observed.outcome != "observed":
            return OutputEvidence(True,observed.programmed,observed.questionable,observed.voltage_v,observed.current_a,"unknown",observed.error)
        if (abs(observed.voltage_v) > max_voltage_v or abs(observed.current_a) > max_current_a
                or abs(observed.voltage_v * observed.current_a) > max_power_w):
            return OutputEvidence(True, observed.programmed, observed.questionable,
                                  observed.voltage_v, observed.current_a, "unknown",
                                  "measured output exceeds caller envelope")
        return observed


def request_output_off(driver, *, max_residual_v, max_residual_a, max_samples=3):
    """Send OFF once, inspect at most max_samples; core timeout bounds each I/O.

    'instrument_below_limits' is only device-reported evidence, not proof of
    electrical isolation, discharged DUT or independent physical safety.
    """
    if any(not _finite(v) or v < 0 for v in (max_residual_v,max_residual_a)):
        raise ConfigurationError("finite nonnegative residual limits required")
    if type(max_samples) is not int or not 1 <= max_samples <= 100:
        raise ConfigurationError("sample budget must be 1..100")
    with driver.session.operation_lock():
        driver._require_methods("OutputSubsystem.state_set")
        try:
            driver.output.state_set(False)
        except ScpiDriverError as exc:
            return OutputEvidence(False,None,None,None,None,"unknown",str(exc))
        for _ in range(max_samples):
            e = observe_output(driver,requested=False)
            if e.outcome != "observed":
                return e
            if not e.programmed and abs(e.voltage_v) <= max_residual_v and abs(e.current_a) <= max_residual_a:
                return OutputEvidence(False,e.programmed,e.questionable,e.voltage_v,e.current_a,"instrument_below_limits")
        return OutputEvidence(False,e.programmed,e.questionable,e.voltage_v,e.current_a,"not_confirmed")
