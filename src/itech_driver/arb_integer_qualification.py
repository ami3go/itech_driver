"""ARB exact integer envelopes bound to documented model and firmware evidence."""
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from scpi_driver_core import ConfigurationError, UnsupportedOperationError
from .capabilities import MODEL_DESCRIPTORS, descriptor_for
from .utils.validation import exact_integer

# Conservative family-level ceilings, not qualified per-command firmware bounds.
# IT-M3900D User Manual V2.6/5,2025, section 4.6.1.
FAMILY_INTEGER_MAX = MappingProxyType({
    "udef_count_set": 200,
    "udef_level_set": 200,
    "udef_level_query": 200,
    "udef_dwell_set": 200,
    "udef_dwell_query": 200,
    "udef_slew_set": 200,
    "udef_slew_query": 200,
    "count_set": 999999,
    "save": 10,
    "recall": 10,
})


@dataclass(frozen=True)
class ArbIntegerBounds:
    minimum: int
    maximum: int
    evidence: str

    def __post_init__(self):
        if (type(self.minimum) is not int or type(self.maximum) is not int
                or not 1 <= self.minimum <= self.maximum):
            raise ConfigurationError("positive ordered integer bounds required")
        if not isinstance(self.evidence, str) or not self.evidence.strip():
            raise ConfigurationError("command-specific evidence required")

    def validate(self, value, method):
        return exact_integer(value, minimum=self.minimum, maximum=self.maximum, name=method)


@dataclass(frozen=True)
class ArbIntegerQualification:
    model: str
    firmware: str
    commands: Mapping[str, ArbIntegerBounds]

    def __post_init__(self):
        if not isinstance(self.model, str) or self.model not in MODEL_DESCRIPTORS:
            raise ConfigurationError("exact rated model required")
        if not isinstance(self.firmware, str) or not self.firmware.strip() or self.firmware.strip().upper() in ("UNKNOWN", "N/A", "NONE"):
            raise ConfigurationError("exact firmware required")
        if not isinstance(self.commands, Mapping):
            raise ConfigurationError("explicit per-command bounds required")
        copy = dict(self.commands)
        for method, bound in copy.items():
            if method not in FAMILY_INTEGER_MAX or not isinstance(bound, ArbIntegerBounds):
                raise ConfigurationError("unknown ARB integer command or invalid bounds")
            if bound.maximum > FAMILY_INTEGER_MAX[method]:
                raise ConfigurationError("qualification cannot exceed conservative family envelope")
        object.__setattr__(self, "commands", MappingProxyType(copy))

    def validate(self, method, value):
        if method not in self.commands:
            raise UnsupportedOperationError(f"{method} lacks exact model/firmware integer bounds")
        return self.commands[method].validate(value, method)

    def check_identity(self, identity):
        if (descriptor_for(identity) is None or identity.model.strip().upper() != self.model
                or identity.firmware_version != self.firmware):
            raise UnsupportedOperationError("ARB integer qualification identity mismatch")


def validate_arb_integer(driver, method, value):
    """Reject invalid parameters before any I/O; validate explicit bound if configured."""
    exact_integer(value, minimum=1, maximum=FAMILY_INTEGER_MAX[method], name=method)
    profile = getattr(driver, "_arb_integer_qualification", None)
    strict = (getattr(driver, "_require_qualified_capabilities", False)
              or getattr(driver, "_require_arb_integer_qualification", False))
    if profile is None:
        if strict:
            raise UnsupportedOperationError("strict ARB operation requires command-specific integer bounds")
        return value
    profile.validate(method, value)
    if (not driver.session.is_connected
            or driver._arb_integer_generation != driver.session.generation):
        raise UnsupportedOperationError("ARB integer qualification requires current-session binding")
    return value
