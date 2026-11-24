"""ITECH IT-M3900D series power supply driver."""

from contextlib import contextmanager
from scpi_driver_core import ScpiDriverError, SafetyGuardError, ConfigurationError, UnsupportedOperationError
from ..method_qualification import MethodQualification, install_subsystem_guards
from ..arb_integer_qualification import ArbIntegerQualification
from ..base import BaseInstrument
from ..capabilities import ApplicationLimits, discover_capabilities, descriptor_for
from ..subsystems.LoggingSubsystem import LoggingSubsystem
from ..subsystems.FetchSubsystem import FetchSubsystem
from ..subsystems.SenseSubsystem import SenseSubsystem
from ..subsystems.MeasurementSubsystem import MeasurementSubsystem
from ..subsystems.ArbSubsystem import ArbSubsystem
from ..subsystems.AbortSubsystem import AbortSubsystem
from ..subsystems.BatterySubsystem import BatterySubsystem
from ..subsystems.IEEE488 import IEEE488
from ..subsystems.InitiateSubsystem import InitiateSubsystem
from ..subsystems.IOConfigSubsystem import IOConfigSubsystem
from ..subsystems.OutputSubsystem import OutputSubsystem
from ..subsystems.SourceSubsystem import SourceSubsystem
from ..subsystems.StatusSubsystem import StatusSubsystem
from ..subsystems.SystemSubsystem import SystemSubsystem
from ..subsystems.TriggerSubsystem import TriggerSubsystem


# Install exactly once when the driver module is imported. Exported subsystem
# classes use the same guard even if callers instantiate them directly.
install_subsystem_guards((
    SystemSubsystem, SourceSubsystem, OutputSubsystem, StatusSubsystem,
    TriggerSubsystem, ArbSubsystem, BatterySubsystem, InitiateSubsystem,
    AbortSubsystem, IOConfigSubsystem, IEEE488, MeasurementSubsystem,
    SenseSubsystem, FetchSubsystem, LoggingSubsystem,
))


class ITM3900D(BaseInstrument):
    """ITECH IT-M3900D series power supply."""
    
    def __init__(self, resource_name: str, timeout: int = 5000, 
                 termination: str = '\n', interface_kwargs: dict = None, *, require_remote: bool = False, application_limits: ApplicationLimits | None = None, require_qualified_capabilities: bool = False, **kwargs):
        self._initialize_policy(require_remote, application_limits, require_qualified_capabilities)
        super().__init__(resource_name, timeout, termination, interface_kwargs, **kwargs)
        try:
            self._initialize_subsystems()
        except BaseException as primary:
            try:
                self.close()
            except Exception as cleanup:
                if hasattr(primary, "add_note"):
                    primary.add_note(f"Subsystem initialization cleanup failed: {cleanup!r}")
                else:
                    primary.cleanup_error = cleanup
            raise

    @staticmethod
    def _validate_policy(require_remote, application_limits, require_qualified_capabilities=False):
        if type(require_qualified_capabilities) is not bool:
            raise ConfigurationError("require_qualified_capabilities must be bool")
        if type(require_remote) is not bool:
            raise ConfigurationError("require_remote must be bool")
        if application_limits is not None and not isinstance(application_limits, ApplicationLimits):
            raise ConfigurationError("application_limits must be ApplicationLimits")

    def _initialize_policy(self, require_remote, application_limits, require_qualified_capabilities=False):
        self._validate_policy(require_remote, application_limits, require_qualified_capabilities)
        self._require_qualified_capabilities = require_qualified_capabilities
        self._method_qualification = None
        self._qualification_generation = None
        self._require_arb_integer_qualification = False
        self._arb_integer_qualification = None
        self._arb_integer_generation = None
        self._application_limits = application_limits or ApplicationLimits()
        self.require_remote = require_remote
        self._mode_request = None
        self._mode_generation = None

    @classmethod
    def _from_live_session(cls, session, *, require_remote, application_limits, require_qualified_capabilities=False):
        """Internal factory adoption; caller owns cleanup until successful return."""
        driver = cls.__new__(cls)
        driver._initialize_policy(require_remote, application_limits, require_qualified_capabilities)
        driver._bind_session(session)
        driver._initialize_subsystems()
        return driver

    def _initialize_subsystems(self):
        # Initialize subsystems
        self.system = SystemSubsystem(self)
        self.source = SourceSubsystem(self)
        self.output = OutputSubsystem(self)
        
        # IT-M3900D specific subsystems
        self.status = StatusSubsystem(self)
        self.trigger = TriggerSubsystem(self)
        self.arb = ArbSubsystem(self)
        self.battery = BatterySubsystem(self)
        self.initiate = InitiateSubsystem(self)
        self.abort = AbortSubsystem(self)
        self.io = IOConfigSubsystem(self)
        self.ieee = IEEE488(self)
        self.measurement = MeasurementSubsystem(self)
        self.sense = SenseSubsystem(self)
        self.fetch = FetchSubsystem(self)
        self.elog = LoggingSubsystem(self, 'ELOG')
        self.dlog = LoggingSubsystem(self, 'DLOG')


    def identity_snapshot(self, *, refresh=False):
        with self.session.operation_lock():
            try:
                identity = super().identity_snapshot(refresh=refresh)
                profile = self._method_qualification
                if profile is not None and (descriptor_for(identity) is None or identity.model.strip().upper() != profile.model or identity.firmware_version != profile.firmware):
                    self._method_qualification = None
                    self._qualification_generation = None
                arb_profile = self._arb_integer_qualification
                if arb_profile is not None:
                    try:
                        arb_profile.check_identity(identity)
                    except UnsupportedOperationError:
                        self._arb_integer_generation = None
                return identity
            except ScpiDriverError:
                self._invalidate_mode()
                self._method_qualification = None
                self._qualification_generation = None
                self._arb_integer_generation = None
                raise

    def bind_arb_integer_qualification(self, profile: ArbIntegerQualification):
        """Bind explicit command bounds to this live identity and generation."""
        with self.session.operation_lock():
            # Failed rebinding must never restore permissive family-only behavior.
            self._require_arb_integer_qualification = True
            self._arb_integer_generation = None
            if not isinstance(profile, ArbIntegerQualification):
                raise ConfigurationError("ArbIntegerQualification required")
            self._arb_integer_qualification = profile
            profile.check_identity(self.identity_snapshot(refresh=True))
            self._arb_integer_generation = self.session.generation

    def bind_method_qualification(self, profile: MethodQualification):
        """Explicit identity read; a failed bind leaves strict mode closed."""
        with self.session.operation_lock():
            self._require_qualified_capabilities = True
            self._method_qualification = None
            self._qualification_generation = None
            if not isinstance(profile, MethodQualification):
                raise ConfigurationError("MethodQualification required")
            identity = self.identity_snapshot(refresh=True)
            if (descriptor_for(identity) is None or identity.model.strip().upper() != profile.model
                    or identity.firmware_version != profile.firmware
                    or self.session.transport.descriptor.kind != profile.interface):
                raise UnsupportedOperationError("method qualification identity or interface mismatch")
            self._method_qualification = profile
            self._qualification_generation = self.session.generation

    def _require_methods(self, *keys):
        """Check the entire compound operation under its caller's operation lock."""
        if not self._require_qualified_capabilities:
            return
        if (self._method_qualification is None or not self.session.is_connected
                or self._qualification_generation != self.session.generation):
            raise UnsupportedOperationError("bind current-session method qualification before subsystem use")
        for key in keys:
            self._method_qualification.require(key)

    @contextmanager
    def _qualified_method_scope(self, key):
        with self.session.operation_lock():
            self._require_methods(key)
            yield

    def model_descriptor(self, *, refresh=True):
        """Return nominal descriptor, or None for an unknown identity."""
        return descriptor_for(self.identity_snapshot(refresh=refresh))

    @property
    def application_limits(self):
        """Immutable application bounds for this driver instance."""
        return self._application_limits

    def discover_capabilities(self, *, application_limits=None):
        if application_limits is None:
            application_limits = self.application_limits
        return discover_capabilities(self, application_limits=application_limits)

    @property
    def requested_mode(self):
        """Last mode request in the live session, not a physical mode readback."""
        if not self.session.is_connected or self._mode_generation != self.session.generation:
            return None
        return self._mode_request

    def _invalidate_mode(self):
        self._mode_request = None
        self._mode_generation = None

    def _request_mode(self, command, mode):
        with self.session.operation_lock():
            self._invalidate_mode()
            super().write_scpi(command)
            self._mode_request = mode
            self._mode_generation = self.session.generation

    def enter_remote(self):
        self._request_mode("SYST:REM", "remote")

    def return_local(self):
        self._request_mode("SYST:LOC", "local")

    def _assert_write_authorized(self) -> None:
        if self.require_remote and self.requested_mode != "remote":
            raise SafetyGuardError("explicit enter_remote() required before writes")

    def _invoke_ieee(self, operation, *args, write=False, invalidate=False):
        with self.session.operation_lock():
            if write:
                self._assert_write_authorized()
            try:
                result = super()._invoke_ieee(operation, *args, write=write, invalidate=invalidate)
            except ScpiDriverError:
                self._invalidate_mode()
                raise
            if invalidate:
                self._invalidate_mode()
            return result

    def write_scpi(self, cmd):
        with self.session.operation_lock():
            normalized = cmd.strip().upper().lstrip(":")
            if normalized in ("SYST:REM", "SYSTEM:REMOTE", "SYST:REMOTE", "SYSTEM:REM"):
                return self.enter_remote()
            if normalized in ("SYST:LOC", "SYSTEM:LOCAL", "SYST:LOCAL", "SYSTEM:LOC"):
                return self.return_local()
            self._assert_write_authorized()
            try:
                super().write_scpi(cmd)
            except ScpiDriverError:
                self._invalidate_mode()
                raise
            if ";" in normalized or normalized in ("*RST", "SYST:PRES", "SYSTEM:PRESET", "SYST:PRESET", "SYSTEM:PRES"):
                self._invalidate_mode()

    def query_scpi(self, cmd, delay=0.0):
        with self.session.operation_lock():
            try:
                return super().query_scpi(cmd, delay)
            except ScpiDriverError:
                self._invalidate_mode()
                raise

    def query_binary(self, *args, **kwargs):
        with self.session.operation_lock():
            try:
                return super().query_binary(*args, **kwargs)
            except ScpiDriverError:
                self._invalidate_mode()
                raise

    @contextmanager
    def remote_mode(self):
        """Request remote, then local on exit if the same session is still live."""
        with self.session.operation_lock():
            if self.requested_mode == "remote":
                raise SafetyGuardError("remote_mode context cannot nest or adopt an existing remote request")
            self.enter_remote()
            generation = self.session.generation
            try:
                yield self
            except BaseException as primary:
                if self.session.is_connected and self.session.generation == generation:
                    try:
                        self.return_local()
                    except Exception as cleanup:
                        if hasattr(primary, "add_note"):
                            primary.add_note(f"return_local failed: {cleanup}")
                raise
            else:
                if self.session.is_connected and self.session.generation == generation:
                    self.return_local()
                else:
                    self._invalidate_mode()
                    raise SafetyGuardError("session changed or disconnected; local mode not requested")
