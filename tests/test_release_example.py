from itech_driver import ITM3900D
from itech_driver.simulator import ItechSimulator


def test_release_documentation_offline_example():
    sim=ItechSimulator()
    with ITM3900D("sim",transport=sim.transport) as driver:
        assert "SIMULATED" in driver.identify()
        assert float(driver.query_scpi("MEAS:VOLT?"))==0.0
        assert sim.transport.history==["*IDN?","MEAS:VOLT?"]
