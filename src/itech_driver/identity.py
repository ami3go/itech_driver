"""Exact supported model matching, separate from transport."""
from scpi_driver_core.models import Identity
from .capabilities import RATINGS


def is_itm3900d(identity: Identity) -> bool:
    return (identity.manufacturer.strip().upper() == "ITECH"
            and identity.model.strip().upper() in RATINGS)
