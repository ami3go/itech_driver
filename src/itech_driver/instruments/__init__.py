"""Instrument implementations and factory functions."""

from typing import Dict, Type, Any, Optional
from ..base import BaseInstrument
from ..instruments.itm3900d import ITM3900D
from ..instruments.generic_scpi import GenericSCPIInstrument

# Instrument registry for factory pattern
INSTRUMENT_REGISTRY: Dict[str, Type[BaseInstrument]] = {
    'IT-M3900D': ITM3900D,
    'IT-M3900': ITM3900D,  # Alias for shorter model name
    'IT3900D': ITM3900D,  # Another common abbreviation
    'Generic': GenericSCPIInstrument,
    'SCPI': GenericSCPIInstrument,  # Alias
}


def list_available_instruments() -> list:
    """Return a list of all supported instrument models."""
    return list(INSTRUMENT_REGISTRY.keys())


def register_instrument(model: str, instrument_class: Type[BaseInstrument]):
    """Register a new instrument type in the registry.

    Args:
        model: Model name or identifier
        instrument_class: The instrument class to register
    """
    INSTRUMENT_REGISTRY[model] = instrument_class


def create_instrument(model: str, resource_name: str, **kwargs) -> BaseInstrument:
    """Factory function to create instrument instances.

    Args:
        model: Instrument model name (e.g., 'IT-M3900D', 'Generic')
        resource_name: VISA resource string
        **kwargs: Additional arguments passed to instrument constructor

    Returns:
        BaseInstrument: Instance of the requested instrument

    Raises:
        ValueError: If the instrument model is not supported
    """
    if model not in INSTRUMENT_REGISTRY:
        available = list_available_instruments()
        raise ValueError(
            f"Unsupported instrument model: {model}. "
            f"Available models: {', '.join(available)}"
        )

    return INSTRUMENT_REGISTRY[model](resource_name, **kwargs)


def auto_detect_instrument(resource_name: str, *, require_remote: bool = False,
                           application_limits=None, require_qualified_capabilities=False, **kwargs) -> BaseInstrument:
    """Probe once, then adopt the same live session for a recognized model.

    Unknown valid identities retain only generic common commands. An explicit
    vendor-specific safety policy cannot be silently discarded on fallback.
    """
    from scpi_driver_core import IdentityError
    from ..identity import is_itm3900d

    ITM3900D._validate_policy(require_remote, application_limits, require_qualified_capabilities)
    temp = GenericSCPIInstrument(resource_name, **kwargs)
    try:
        identity = temp.identity_snapshot()
        if not is_itm3900d(identity):
            if require_remote or application_limits is not None or require_qualified_capabilities:
                raise IdentityError("vendor safety policy requires recognized ITECH model")
            return temp
        # Only this factory holds temp. The session (including its immutable
        # identity cache) is transferred, not the transport reopened.
        driver = ITM3900D._from_live_session(
            temp.session, require_remote=require_remote, application_limits=application_limits,
            require_qualified_capabilities=require_qualified_capabilities
        )
        return driver
    except BaseException as primary:
        try:
            temp.close()
        except Exception as cleanup:
            if hasattr(primary, 'add_note'):
                primary.add_note(f'Identification cleanup failed: {cleanup!r}')
            else:
                primary.cleanup_error = cleanup
        raise


def create_instrument_from_idn(resource_name: str, **kwargs) -> BaseInstrument:
    """Detect a supported model or return a generic driver for a valid unknown ID."""
    return auto_detect_instrument(resource_name, **kwargs)


# Export specific instrument classes for direct import
__all__ = [
    'ITM3900D',
    'GenericSCPIInstrument',
    'INSTRUMENT_REGISTRY',
    'list_available_instruments',
    'register_instrument',
    'create_instrument',
    'auto_detect_instrument',
    'create_instrument_from_idn',
]
