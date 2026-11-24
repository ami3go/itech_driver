import pytest
from scpi_driver_core import ConfigurationError
from itech_driver.waveform import Envelope, Sweep


def plan(sweep,budget=20):
    return sweep.commands(Envelope(10,0.001,10),min_frequency_hz=1,
                          max_frequency_hz=100,amplitude_convention="peak_to_peak",
                          max_steps=budget)


def test_sweep_plan():
    assert plan(Sweep(4,5,10,20,2,0.1)) == (
        "ARB:SWE:AMPL 4","ARB:SWE:OFFS 5","ARB:SWE:STAR 10",
        "ARB:SWE:END 20","ARB:SWE:STEP:LEV 2","ARB:SWE:STEP:WIDT 0.1")


@pytest.mark.parametrize("sweep",[
    Sweep(4,5,20,10,2,0.1),Sweep(4,5,10,20,0,0.1),
    Sweep(4,5,10,20,11,0.1),Sweep(4,5,10,101,2,0.1),
    Sweep(12,5,10,20,2,0.1),Sweep(4,5,10,20,2,0),
    Sweep(4,5,10,20,0.001,0.1)])
def test_invalid_sweep(sweep):
    with pytest.raises(ConfigurationError):
        plan(sweep)
