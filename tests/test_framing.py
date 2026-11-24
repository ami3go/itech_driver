import pytest
from itech_driver import ITM3900D
from itech_driver.exceptions import InstrumentNotFoundError
from scpi_driver_core import ConfigurationError
from scpi_driver_core.simulation import ScriptedScpiTransport


@pytest.mark.parametrize("ending",["\n","\r\n","\r"])
def test_explicit_framing(ending):
    t=ScriptedScpiTransport()
    with ITM3900D("sim",transport=t,termination=ending) as d:
        assert d.client.codec.encode_command("*IDN?")==b"*IDN?"+ending.encode()
        assert d.client.codec.decode_response(b"ITECH"+ending.encode())=="ITECH"


@pytest.mark.parametrize("ending",["","abc","\n\n","\x00","é",None])
def test_unsupported_termination_before_open(ending):
    t=ScriptedScpiTransport()
    with pytest.raises(ConfigurationError):
        ITM3900D("sim",transport=t,termination=ending)
    assert not t.is_open


class FailingManager:
    def open_resource(self, name, **kwargs):
        assert kwargs["read_termination"] is None
        assert kwargs["write_termination"] is None
        raise RuntimeError("backend refused raw framing")


def test_backend_framing_failure_visible():
    with pytest.raises(InstrumentNotFoundError) as exc:
        ITM3900D("USB0::1::2::INSTR",resource_manager=FailingManager())
    assert "backend refused raw framing" in str(exc.value)
