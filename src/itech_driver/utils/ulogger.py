"""Logging configuration without taking ownership of caller handlers."""

import logging
import sys
from pathlib import Path
from threading import RLock

_LOCK = RLock()
_OWNER = "_itech_driver_setup_owned"


def setup_logging(level: int = logging.INFO, log_file: str | Path | None = None) -> None:
    """Replace only handlers installed by this helper; caller handlers are retained.

    If opening a new file fails, preserve the existing configuration.
    """
    logger = logging.getLogger("itech_driver")
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    with _LOCK:
        handlers: list[logging.Handler] = []
        try:
            handlers.append(logging.StreamHandler(sys.stdout))
            if log_file is not None:
                handlers.append(logging.FileHandler(log_file))
            for handler in handlers:
                handler.setFormatter(formatter)
                setattr(handler, _OWNER, True)
            logger.setLevel(level)
        except BaseException:
            for handler in handlers:
                handler.close()
            raise
        for handler in logger.handlers[:]:
            if getattr(handler, _OWNER, False) is True:
                logger.removeHandler(handler)
                handler.close()
        for handler in handlers:
            logger.addHandler(handler)
        logger.propagate = False
