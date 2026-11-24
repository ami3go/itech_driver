import pytest
from scpi_driver_core import UnsupportedOperationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


def test_unqualified_generic_delay_does_not_send():
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(UnsupportedOperationError):
            d.trigger.delay_set(0.1)
        with pytest.raises(UnsupportedOperationError):
            d.trigger.delay_query()
        assert t.history == []
