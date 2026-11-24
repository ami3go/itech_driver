import pytest
from itech_driver import ITM3900D
from scpi_driver_core import UnsupportedOperationError
from scpi_driver_core.simulation import ScriptedScpiTransport


def test_battery_capability_claims_agree_with_implementation():
    t = ScriptedScpiTransport()
    with ITM3900D("sim",transport=t) as d:
        assert d.battery.simulation_supported is False
        assert d.battery.execution_supported is False
        with pytest.raises(UnsupportedOperationError):
            d.battery.state_set(True)
        with pytest.raises(UnsupportedOperationError):
            d.battery.state_query()
        assert t.history == []
