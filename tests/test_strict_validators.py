import pytest
from itech_driver import ITM3900D
from itech_driver.capabilities import Range
from itech_driver.exceptions import ValidationError
from itech_driver.utils.validation import (validate_voltage, validate_current,
    validate_channel, validate_range, exact_integer, strict_bool, nonnegative_number)
from scpi_driver_core.simulation import ScriptedScpiTransport


@pytest.mark.parametrize("fn", [validate_voltage, validate_current])
def test_explicit_bounds_required(fn):
    with pytest.raises(ValidationError):
        fn(1)
    assert fn(0, 0, 5) == 0
    assert fn(5, 0, 5) == 5
    with pytest.raises(ValidationError):
        fn(6, 0, 5)


@pytest.mark.parametrize("bad", [True, False, "1", float("nan"), float("inf"), 10**1000])
def test_invalid_numeric_before_io(bad):
    with pytest.raises(ValidationError):
        validate_range(bad, (0, 5), "value")
    with pytest.raises(ValidationError):
        nonnegative_number(bad)
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ValidationError):
            d.source.voltage_set(bad)
    assert t.history == []


@pytest.mark.parametrize("bad", [0, 2, True, 1.0, 1.5, "1", -1])
def test_exact_single_channel(bad):
    with pytest.raises(ValidationError):
        validate_channel(bad, 1)
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ValidationError):
            d.source.current_query(bad)
        with pytest.raises(ValidationError):
            d.output.state_set(False, bad)
    assert t.history == []


def test_no_default_channel_count_and_range_validation():
    with pytest.raises(ValidationError):
        validate_channel(1)
    with pytest.raises(ValidationError):
        Range(2, 1)
    with pytest.raises(ValidationError):
        Range(0, float("inf"))
    assert validate_channel(1, 1) == 1
    assert exact_integer(2, minimum=1, maximum=2) == 2
    assert strict_bool(0) is False
    assert strict_bool(True) is True
    with pytest.raises(ValidationError):
        strict_bool(1.0)
