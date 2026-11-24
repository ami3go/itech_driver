import pytest
from scpi_driver_core import ConfigurationError
from itech_driver.waveform import Envelope, ConstantDwell


def test_cdw_pair_order_and_setup():
    plan = ConstantDwell((1,2,3,4),0.01)
    envelope = Envelope(10,0.001,10)
    assert plan.pairs(envelope,max_points=4) == ((1,2),(3,4))
    assert plan.setup_commands(envelope,max_points=4) == ("ARB:CDW:POIN 4","ARB:CDW:DWEL 0.01")


@pytest.mark.parametrize("levels,dwell",[((),0.01),((1,2,3),0.01),((1,2,3,4,5,6),0.01),
    ((1,11),0.01),((1,float("nan")),0.01),((1,2),0),((1,2),float("inf"))])
def test_invalid_cdw(levels,dwell):
    with pytest.raises(ConfigurationError):
        ConstantDwell(levels,dwell).pairs(Envelope(10,0.001,10),max_points=4)
