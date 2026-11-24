import pytest
from scpi_driver_core import ConfigurationError
from itech_driver.waveform import Envelope, Sine


def plan(sine, convention="peak_to_peak"):
    return sine.commands(Envelope(10,0.001,10),min_frequency_hz=0.1,
                         max_frequency_hz=100,amplitude_convention=convention)


def test_sine_plan_and_conventions():
    assert plan(Sine(6,5,10)) == ("ARB:SIN:AMPL 6","ARB:SIN:OFFS 5","ARB:SIN:FREQ 10")
    assert plan(Sine(6,5,10),"peak")[0] == "ARB:SIN:AMPL 3.0"


@pytest.mark.parametrize("sine",[Sine(12,5,10),Sine(6,1,10),Sine(6,8,10),
                                 Sine(6,5,101),Sine(6,5,0),Sine(float("nan"),5,10)])
def test_invalid_sine(sine):
    with pytest.raises(ConfigurationError):
        plan(sine)


def test_unknown_amplitude_convention():
    with pytest.raises(ConfigurationError):
        plan(Sine(6,5,10),"unknown")
