import pytest
from scpi_driver_core import UnsupportedOperationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


def test_logging_abort_is_not_speculatively_transmitted():
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        for abort in (d.abort.dlog, d.abort.elog):
            with pytest.raises(UnsupportedOperationError):
                abort()
        assert t.history == []
