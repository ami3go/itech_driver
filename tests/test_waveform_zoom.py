import pytest
from scpi_driver_core import ConfigurationError
from itech_driver.waveform import Zoom


def plan(z):
    # Artificial test envelope; not an IT-M3900D specification.
    return z.commands(coefficient_min=0.5,coefficient_max=2,integer_min=-10,integer_max=10)


def test_zoom_candidate_plan():
    assert plan(Zoom(1.2,8,-8))==("ARB:ZOOM:COF 1.2","ARB:ZOOM:LIM:POS 8","ARB:ZOOM:LIM:NEG -8")


@pytest.mark.parametrize("z",[Zoom(float("nan"),8,-8),Zoom(3,8,-8),Zoom(1,11,-8),
                            Zoom(1,3,4),Zoom(1,1.5,-8),Zoom(True,8,-8)])
def test_invalid_zoom(z):
    with pytest.raises(ConfigurationError):
        plan(z)
