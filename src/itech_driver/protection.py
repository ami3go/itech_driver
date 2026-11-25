"""Explicit command-specific protection evidence; no speculative range probes."""
from dataclasses import dataclass
from types import MappingProxyType
from scpi_driver_core import ConfigurationError, UnsupportedOperationError
from .capabilities import MODEL_DESCRIPTORS, Range
from .command_specs import command_spec

# IT-M3900D Programming Guide V1.4/09,2024 pp.46–47,51–52,
# 65–66,70–71,80: threshold queries have no MIN/MAX argument.
PROTECTION_THRESHOLDS = MappingProxyType({
    "ovp": (command_spec("SourceSubsystem.ovp_set").header, "voltage", "65–66"),
    "ocp": (command_spec("SourceSubsystem.ocp_set").header, "current", "46–47"),
    "opp": (command_spec("SourceSubsystem.opp_threshold_set").header, "power", "80"),
    "uvp": (command_spec("SourceSubsystem.uvp_set").header, "voltage", "70–71"),
    "ucp": (command_spec("SourceSubsystem.ucp_set").header, "current", "51–52"),
})


@dataclass(frozen=True)
class ProtectionThresholdQualification:
    """Caller-supplied range and provenance for one exact model/firmware/command.

    The driver validates the declared envelope and its binding, not the
    authenticity of the external evidence. No built-in firmware claims.
    """
    model: str
    firmware: str
    protection: str
    bounds: Range
    evidence: str

    def __post_init__(self):
        if not isinstance(self.model, str) or self.model not in MODEL_DESCRIPTORS:
            raise ConfigurationError("recognized exact model required")
        if not isinstance(self.firmware, str) or not self.firmware.strip() or self.firmware.upper() in ("UNKNOWN", "N/A"):
            raise ConfigurationError("exact qualified firmware required")
        if not isinstance(self.protection, str) or self.protection not in PROTECTION_THRESHOLDS:
            raise ConfigurationError("known protection threshold required")
        if not isinstance(self.bounds, Range) or self.bounds.minimum < 0:
            raise ConfigurationError("explicit nonnegative command-specific bounds required")
        if not isinstance(self.evidence, str) or not self.evidence.strip():
            raise ConfigurationError("external range evidence reference required")


def set_protection_threshold(driver, protection, value, qualification):
    if not isinstance(qualification, ProtectionThresholdQualification) or qualification.protection != protection:
        raise UnsupportedOperationError(f"{protection} threshold requires matching model/firmware range qualification")
    qualification.bounds.validate(value)
    header, quantity, _ = PROTECTION_THRESHOLDS[protection]
    application = getattr(driver.application_limits, quantity)
    if application is not None and value > application.maximum:
        raise ConfigurationError("protection threshold exceeds application ceiling")
    with driver.session.operation_lock():
        method = "SourceSubsystem." + ("opp_threshold" if protection == "opp" else protection) + "_set"
        driver._require_methods(method)
        driver._assert_write_authorized()
        identity = driver.identity_snapshot()
        if (identity.manufacturer.strip().upper() != "ITECH"
                or identity.model.strip().upper() != qualification.model
                or identity.firmware_version != qualification.firmware):
            raise UnsupportedOperationError("protection qualification does not match identified model and firmware")
        driver._require_methods(method)
        driver.write_scpi(f"{header} {value}")
