import pytest
from scpi_driver_core import ConfigurationError
from itech_driver.waveform import Envelope, Pulse, Sine, Sequence, SequenceStep


def plan(steps,**overrides):
    kwargs=dict(max_steps=3,max_repeats=5,first_index=1,min_frequency_hz=1,
                max_frequency_hz=100,amplitude_convention="peak_to_peak")
    kwargs.update(overrides)
    return Sequence(steps).commands(Envelope(10,0.001,10),**kwargs)


def test_ordered_sequence():
    pulse=Pulse(1,0.1,0.01,5,0.2,0.1,0.01)
    sine=Sine(4,5,10)
    assert plan((SequenceStep(pulse,2),SequenceStep(sine,3))) == (
        "ARB:SEQ:LENG 2","ARB:SEQ:SEL 1","ARB:SEQ:FUNC PULS","ARB:SEQ:COUN 2",
        "ARB:SEQ:PULS:STAR:LEV 1","ARB:SEQ:PULS:STAR:TIME 0.1",
        "ARB:SEQ:PULS:STAR:SLEW 0.01","ARB:SEQ:PULS:TOP:LEV 5",
        "ARB:SEQ:PULS:TOP:TIME 0.2","ARB:SEQ:PULS:END:TIME 0.1",
        "ARB:SEQ:PULS:END:SLEW 0.01","ARB:SEQ:SEL 2","ARB:SEQ:FUNC SIN",
        "ARB:SEQ:COUN 3","ARB:SEQ:SIN:AMPL 4","ARB:SEQ:SIN:OFFS 5","ARB:SEQ:SIN:FREQ 10")


@pytest.mark.parametrize("repeats",[0,6,True,1.5])
def test_invalid_repeats(repeats):
    with pytest.raises(ConfigurationError):
        plan((SequenceStep(Sine(4,5,10),repeats),))


def test_bounds_and_index():
    step=SequenceStep(Sine(4,5,10),1)
    for steps,kwargs in [((),{}),((step,)*4,{}),((step,),{"first_index":2})]:
        with pytest.raises(ConfigurationError):
            plan(steps,**kwargs)
