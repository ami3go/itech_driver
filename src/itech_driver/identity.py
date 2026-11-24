"""Exact model matching, separate from transport and firmware qualification."""
from scpi_driver_core.models import Identity
from .capabilities import descriptor_for


def is_itm3900d(identity: Identity) -> bool:
    return descriptor_for(identity) is not None
