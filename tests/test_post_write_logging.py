import logging

from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


class FailingHandler(logging.Handler):
    def emit(self, record):
        raise RuntimeError("logging sink unavailable")


def test_write_does_not_depend_on_adapter_logging():
    transport = ScriptedScpiTransport().on("*CLS")
    logger = logging.getLogger("itech_driver.base")
    handler = FailingHandler()
    previous = logger.level
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    try:
        with ITM3900D("sim", transport=transport) as driver:
            driver.write_scpi("*CLS")
            assert transport.history == ["*CLS"]
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous)
