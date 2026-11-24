import pytest
from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("setter,query,wire,question,reply,value",[
    ("reverse_set","reverse_query","IO:REVE 1,1","IO:REVE? 1","ON",True),
    ("pin_function_set","pin_function_query","IO:TYPE 3,EXTTrig","IO:TYPE? 3","EXTTrig","EXTT"),
    ("output_level_set","output_level_query","IO:OUTP:LEV 1,1","IO:OUTP:LEV? 1","HIGH",True)])
def test_pin_methods(setter,query,wire,question,reply,value):
    pin=3 if setter=="pin_function_set" else 1
    t=ScriptedScpiTransport().on(wire).on(question,reply)
    with ITM3900D("sim",transport=t) as d:
        getattr(d.io,setter)(pin,value)
        assert getattr(d.io,query)(pin)==value
        assert t.history==[wire,question]


def test_pulse_range_and_input():
    t=ScriptedScpiTransport().on("IO:PULS:WIDT? 3,MIN","0").on("IO:PULS:WIDT? 3,MAX","2").on("IO:PULS:WIDT 3,1").on("IO:INP:LEV? 3","LOW")
    with ITM3900D("sim",transport=t) as d:
        d.io.pulse_width_set(3,1)
        assert d.io.input_level_query(3) is False
        with pytest.raises(ConfigurationError):
            d.io.pulse_width_set(3,3)


def test_trigger_and_pwm_readback():
    t=ScriptedScpiTransport().on("IO:TRIG:TYPE TIN").on("IO:TRIG:TYPE?","TIN").on("IO:TRIG:SOUR LIST").on("IO:TRIG:SOUR?","LIST").on("IO:PWM? 2","1").on("IO:PWM:FREQ? 2","100").on("IO:PWM:DUTY? 2","50")
    with ITM3900D("sim",transport=t) as d:
        d.io.trigger_type_set("TIN")
        assert d.io.trigger_type_query()=="TIN"
        d.io.trigger_source_set("LIST")
        assert d.io.trigger_source_query()=="LIST"
        assert d.io.pwm_enable_query(2)
        assert d.io.pwm_freq_query(2)==100
        assert d.io.pwm_duty_query(2)==50


def test_invalid_inputs_and_readback():
    t=ScriptedScpiTransport().on("IO:INP:LEV? 1","UNKNOWN")
    with ITM3900D("sim",transport=t) as d:
        with pytest.raises(ConfigurationError):
            d.io.pin_function_set(0,"SYON")
        with pytest.raises(ConfigurationError):
            d.io.trigger_type_set("TIN;*RST")
        with pytest.raises(ConfigurationError):
            d.io.output_level_set(1,"LOW")
        assert t.history==[]
        with pytest.raises(ResponseParseError):
            d.io.input_level_query(1)
