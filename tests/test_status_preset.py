import pytest
from scpi_driver_core import UnsupportedOperationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


def test_explicit_status_preset_only():
    t = ScriptedScpiTransport().on("STAT:PRES")
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(UnsupportedOperationError):
            d.system.preset()
        assert t.history == []
        d.status.preset()
        assert t.history == ["STAT:PRES"]
