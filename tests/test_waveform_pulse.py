import pytest
from scpi_driver_core import ConfigurationError
from itech_driver.waveform import Envelope, Pulse


def test_pulse_plan():
    plan = Pulse(1,0.1,0.01,5,0.2,0.1,0.01).commands(Envelope(10,0.001,10))
    assert plan == ("ARB:PULS:STAR:LEV 1","ARB:PULS:STAR:TIME 0.1",
                    "ARB:PULS:STAR:SLEW 0.01","ARB:PULS:TOP:LEV 5",
                    "ARB:PULS:TOP:TIME 0.2","ARB:PULS:END:TIME 0.1",
                    "ARB:PULS:END:SLEW 0.01")


@pytest.mark.parametrize("level",[-1,11,float("nan"),True])
def test_invalid_pulse_level(level):
    with pytest.raises(ConfigurationError):
        Pulse(1,0.1,0.01,level,0.2,0.1,0.01).commands(Envelope(10,0.001,10))


def test_invalid_pulse_time():
    with pytest.raises(ConfigurationError):
        Pulse(1,0.1,0.0001,5,0.2,0.1,0.01).commands(Envelope(10,0.001,10))
