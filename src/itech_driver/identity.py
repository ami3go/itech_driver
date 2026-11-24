"""ITECH model identity matching, separate from transport."""
import re
from scpi_driver_core.models import Identity


def is_itm3900d(identity: Identity) -> bool:
    manufacturer = identity.manufacturer.strip().upper()
    model = identity.model.strip().upper()
    return bool(re.match(r"^ITECH(?:\b|$)", manufacturer) and
                re.fullmatch(r"IT-?M?390[0-9]D(?:-[A-Z0-9.]+)*", model))
