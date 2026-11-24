from pathlib import Path
import pytest
from itech_driver import ITM3900D

pytestmark = [pytest.mark.integration, pytest.mark.visa_sim]


@pytest.mark.parametrize("resource", [
    pytest.param("USB0::0x1234::0x5678::SIM001::INSTR", id="usbtmc"),
    pytest.param("TCPIP0::127.0.0.1::inst0::INSTR", id="visa-lan"),
])
def test_visa_interface(resource):
    fixture = Path(__file__).with_name("itech_sim.yaml").resolve()
    with ITM3900D(resource, timeout=1000, visa_library=f"{fixture}@sim") as d:
        assert d.identify() == "ITECH,IT-M3902D-80-40,SIM001,1.0"
        d.source.voltage_set(2.5)
        assert d.source.voltage_query() == pytest.approx(2.5)
        assert d.output.state_query() is False
    assert not d.session.is_connected
