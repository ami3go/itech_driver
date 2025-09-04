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


def auto_detect_instrument(resource_name: str, **kwargs) -> BaseInstrument:
    """Auto-detect instrument type and return appropriate instance.

    This function tries to identify the instrument by querying its IDN string
    and returns the most specific instrument class available.

    Args:
        resource_name: VISA resource string
        **kwargs: Additional arguments passed to instrument constructor

    Returns:
        BaseInstrument: Detected instrument instance or GenericSCPIInstrument
    """
    # Create a temporary generic instrument to query IDN
    temp_instr = GenericSCPIInstrument(resource_name, **kwargs)

    try:
        idn = temp_instr.identify().upper()

        # Check for specific instrument models
        if any(model in idn for model in ['IT-M3900D', 'ITM3900D', 'IT3900D']):
            return ITM3900D(resource_name, **kwargs)
        elif 'ITECH' in idn:
            # For other ITECH instruments, return generic but with brand awareness
            return BaseInstrument(resource_name, **kwargs)
        else:
            # Return generic instrument for unknown models
            return temp_instr

    except Exception as e:
        # If identification fails, return generic instrument
        print(f"Warning: Could not identify instrument: {e}")
        return temp_instr


def create_instrument_from_idn(resource_name: str, **kwargs) -> BaseInstrument:
    """Create instrument based on IDN string with fallback options.

    This is similar to auto_detect_instrument but provides more control
    over the detection process.

    Args:
        resource_name: VISA resource string
        **kwargs: Additional arguments passed to instrument constructor

    Returns:
        BaseInstrument: Appropriate instrument instance
    """
    try:
        # Try auto-detection first
        return auto_detect_instrument(resource_name, **kwargs)
    except Exception as e:
        print(f"Auto-detection failed: {e}. Using generic instrument.")
        return BaseInstrument(resource_name, **kwargs)


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