from pathlib import Path

import pytest

from itech_driver import ITM3900D
from scpi_driver_core.transport.visa import VisaTransport

pytestmark = [pytest.mark.integration, pytest.mark.visa_sim]


def test_real_core_visa_transport_path():
    fixture = Path(__file__).with_name("itech_sim.yaml").resolve()
    with ITM3900D("GPIB0::9::INSTR", timeout=1000, visa_library=f"{fixture}@sim") as d:
        assert isinstance(d.session.transport, VisaTransport)
        assert d.identify() == "ITECH,IT-M3900D,SIM001,1.0"
        d.source.voltage_set(2.5)
        assert d.source.voltage_query() == pytest.approx(2.5)
        d.output.state_set(False)
        assert d.output.state_query() is False
