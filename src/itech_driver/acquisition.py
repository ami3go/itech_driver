"""Serialized acquisition configuration and arming, without software trigger."""
from dataclasses import dataclass
from scpi_driver_core import ConfigurationError
from .subsystems.SenseSubsystem import _points, _offset, _interval
from .subsystems.TriggerSubsystem import TriggerSubsystem


@dataclass(frozen=True)
class AcquisitionConfig:
    points: int
    offset: int
    interval: float
    source: str

    def __post_init__(self):
        _points(self.points)
        _offset(self.offset)
        _interval(self.interval)
        token = TriggerSubsystem._normalize_source("ACQ", self.source)
        if token == "IMM":
            raise ConfigurationError("compound configure-and-arm excludes immediate trigger")
        object.__setattr__(self, "source", token)


def configure_and_arm(driver, config: AcquisitionConfig) -> None:
    """Transmit at most five commands under the shared core operation lock.

    Successful return confirms transmission only, not hardware readiness.
    Each transaction uses the finite configured core timeout. No replay,
    reconnect, reset, software trigger or inferred acquisition readback.
    """
    if not isinstance(config, AcquisitionConfig):
        raise ConfigurationError("validated AcquisitionConfig required")
    with driver.session.operation_lock():
        driver._assert_write_authorized()
        driver._require_methods("SenseSubsystem.acquisition_points_set",
            "SenseSubsystem.acquisition_offset_set", "SenseSubsystem.acquisition_interval_set",
            "TriggerSubsystem.acquire_start", "TriggerSubsystem.acquire_source_set", "TriggerSubsystem.acquire_arm")
        driver.sense.acquisition_points_set(config.points)
        driver.sense.acquisition_offset_set(config.offset)
        driver.sense.acquisition_interval_set(config.interval)
        driver.trigger.acquire_start(config.source)
