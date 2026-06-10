"""Software safety policy for high-power IT-M3900D operation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyPolicy:
    """Configurable software safety limits.

    The policy is a software guard only. It does not replace external fuses,
    interlocks, emergency-stop circuits, proper wiring, or operator training.
    """

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
    unsafe_allow_output_on_without_confirm: bool = False
