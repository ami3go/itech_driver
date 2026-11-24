import pytest
from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("pin", [0, 6])
def test_valid_pin_boundaries(pin):
    commands = [f"IO:SELect {pin}", f"IO:PWM:ENABle {pin},1",
                f"IO:PWM:FREQuency {pin},2", f"IO:PWM:FREQuency {pin},21000",
                f"IO:PWM:DUTY {pin},1", f"IO:PWM:DUTY {pin},100"]
    t = ScriptedScpiTransport()
    for command in commands:
        t.on(command)
    with ITM3900D("sim", transport=t) as d:
        d.io.select(pin)
        d.io.pwm_enable(pin, True)
        d.io.pwm_freq_set(pin, 2)
        d.io.pwm_freq_set(pin, 21000)
        d.io.pwm_duty_set(pin, 1)
        d.io.pwm_duty_set(pin, 100)
        assert t.history == commands


@pytest.mark.parametrize("pin", [-1, 7, 1.5, True, "0;*RST"])
def test_invalid_pins(pin):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        for method, args in [(d.io.select,(pin,)), (d.io.pwm_enable,(pin,True)),
                             (d.io.pwm_freq_set,(pin,100)), (d.io.pwm_duty_set,(pin,50))]:
            with pytest.raises(ConfigurationError):
                method(*args)
        assert t.history == []


def test_invalid_pwm_values():
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        for value in (0, 21001, float("nan"), float("inf"), True):
            with pytest.raises(ConfigurationError):
                d.io.pwm_freq_set(0, value)
        for value in (0, 101, 10.5, True):
            with pytest.raises(ConfigurationError):
                d.io.pwm_duty_set(0, value)
        with pytest.raises(ConfigurationError):
            d.io.pwm_enable(0, "OFF")
        assert t.history == []


def test_invalid_selected_pin_reply():
    t = ScriptedScpiTransport().on("IO:SELect?", "7")
    with ITM3900D("sim", transport=t) as d, pytest.raises(ResponseParseError):
        d.io.select_query()
