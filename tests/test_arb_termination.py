import pytest
from scpi_driver_core import UnsupportedOperationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("mode", [0, 1, "LAST", "NORMAL", "OFF"])
def test_unqualified_termination_has_no_io(mode):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(UnsupportedOperationError):
            d.arb.terminate_last_set(mode)
        with pytest.raises(UnsupportedOperationError):
            d.arb.terminate_last_query()
        assert t.history == []
