import pytest
from scpi_driver_core import ConfigurationError, UnsupportedOperationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("enable,token", [(True, 1), (False, 0), (1, 1), (0, 0)])
def test_remote_sense_set(enable, token):
    command = f"SOUR:REM:SENS:STAT {token}"
    t = ScriptedScpiTransport().on(command)
    with ITM3900D("sim", transport=t) as d:
        d.source.remote_sense_set(enable)
        assert t.history == [command]


def test_unsupported_query_and_invalid_inputs_do_not_send():
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(UnsupportedOperationError):
            d.source.remote_sense_query()
        with pytest.raises(ConfigurationError):
            d.source.remote_sense_set("OFF")
        with pytest.raises(ConfigurationError):
            d.source.remote_sense_set(True, channel=2)
        assert t.history == []
