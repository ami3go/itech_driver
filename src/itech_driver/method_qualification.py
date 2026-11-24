"""Explicit model, firmware and interface evidence for typed subsystem methods."""
from dataclasses import dataclass
from functools import wraps
import inspect
from types import MappingProxyType
from typing import Mapping

from scpi_driver_core import ConfigurationError, UnsupportedOperationError
from .capabilities import CapabilityState, MODEL_DESCRIPTORS

from .command_specs import COMMAND_SPECS, ResultKind

# Identity is available for binding; LoggingConfig.commands is an offline planner.
# Logging instances use independent evidence even though their Python API is shared.
def _qualification_keys():
    for key, spec in COMMAND_SPECS.items():
        if key == "IEEE488.idn" or spec.kind is ResultKind.PLANNER:
            continue
        if key.startswith("LoggingSubsystem."):
            name = key.split(".", 1)[1]
            for kind in ("DLOG", "ELOG"):
                yield f"LoggingSubsystem.{kind}.{name}"
        else:
            yield key


METHOD_KEYS = frozenset(_qualification_keys())
RESTRICTED = frozenset(
    key for key, spec in COMMAND_SPECS.items() if spec.kind is ResultKind.RESTRICTED
) | frozenset(("LoggingSubsystem.DLOG.raw_data_query",))


@dataclass(frozen=True)
class MethodEvidence:
    state: CapabilityState
    reference: str

    def __post_init__(self):
        if not isinstance(self.state, CapabilityState):
            raise ConfigurationError("explicit CapabilityState required")
        if not isinstance(self.reference, str) or not self.reference.strip():
            raise ConfigurationError("evidence reference required")


@dataclass(frozen=True)
class MethodQualification:
    model: str
    firmware: str
    interface: str
    methods: Mapping[str, MethodEvidence]

    def __post_init__(self):
        if not isinstance(self.model, str) or self.model not in MODEL_DESCRIPTORS:
            raise ConfigurationError("exact rated model required")
        if not isinstance(self.firmware, str) or not self.firmware.strip() or self.firmware.strip().upper() in ("UNKNOWN", "N/A", "NONE"):
            raise ConfigurationError("exact firmware required")
        if not isinstance(self.interface, str) or not self.interface.strip():
            raise ConfigurationError("exact core transport descriptor kind required")
        if not isinstance(self.methods, Mapping):
            raise ConfigurationError("method evidence map required")
        copy = dict(self.methods)
        for key, evidence in copy.items():
            if key not in METHOD_KEYS or not isinstance(evidence, MethodEvidence):
                raise ConfigurationError(f"unknown method or invalid evidence: {key}")
            if key in RESTRICTED and evidence.state is CapabilityState.SUPPORTED:
                raise ConfigurationError(f"quarantined operation cannot be enabled: {key}")
        object.__setattr__(self, "methods", MappingProxyType(copy))

    def state(self, key):
        if key in RESTRICTED:
            return CapabilityState.UNQUALIFIED
        evidence = self.methods.get(key)
        return evidence.state if evidence is not None else CapabilityState.UNKNOWN

    def require(self, key):
        state = self.state(key)
        if state is not CapabilityState.SUPPORTED:
            raise UnsupportedOperationError(f"{key} is {state.value} for {self.model}/{self.firmware}/{self.interface}")


def install_subsystem_guards(classes):
    """Install guards on the actual subsystem classes, including direct instances.

    No per-instance closure or reflection-based replacement is needed during
    instrument construction. This preserves signatures and isinstance checks.
    """
    def guard(method, prefix):
        @wraps(method)
        def wrapped(self, *args, **kwargs):
            key = prefix
            if prefix.startswith("LoggingSubsystem."):
                key = "LoggingSubsystem." + self._kind + "." + method.__name__
            scope = getattr(self._p, "_qualified_method_scope", None)
            if scope is None:
                # Compatibility for non-ITECH parents and standalone mocks.
                return method(self, *args, **kwargs)
            with scope(key):
                return method(self, *args, **kwargs)
        return wrapped
    found = set()
    for cls in classes:
        prefix = cls.__name__
        for name, method in inspect.getmembers(cls, inspect.isfunction):
            if name.startswith("_") or (prefix == "IEEE488" and name == "idn"):
                continue
            key = prefix + "." + name
            keys = ({"LoggingSubsystem.ELOG." + name, "LoggingSubsystem.DLOG." + name}
                    if prefix == "LoggingSubsystem" else {key})
            if not keys <= METHOD_KEYS:
                raise ConfigurationError(f"missing subsystem qualification key {key}")
            setattr(cls, name, guard(method, key))
            found.update(keys)
    if found != METHOD_KEYS:
        raise ConfigurationError("subsystem qualification inventory mismatch")
