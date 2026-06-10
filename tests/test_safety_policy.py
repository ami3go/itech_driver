import pytest

from itm3900d import ITM3900D, SafetyPolicy
from itm3900d.exceptions import OutputEnableConfirmationRequired, OutputEnableNotAllowedError, SafetyLimitError


def test_output_on_confirmation_required_even_when_allowed():
    psu = ITM3900D(dry_run=False, session=None, resource="DRYRUN", safety=SafetyPolicy(max_voltage_v=10, max_current_a=1, max_power_w=10), allow_output_enable=True)
    psu.dry_run = True
    psu.open()
    psu.configure_cv(5, 0.5, 5)
    psu.dry_run = False
    with pytest.raises(OutputEnableConfirmationRequired):
        psu.output_on(confirm=False)


def test_output_on_requires_allow_output_enable():
    psu = ITM3900D(dry_run=True, safety=SafetyPolicy(max_voltage_v=10, max_current_a=1, max_power_w=10), allow_output_enable=False)
    psu.open()
    psu.configure_cv(5, 0.5, 5)
    with pytest.raises(OutputEnableNotAllowedError):
        psu.output_on(confirm=True)


def test_voltage_limit_enforced():
    psu = ITM3900D(dry_run=True, strict=False, safety=SafetyPolicy(max_voltage_v=5))
    psu.open()
    with pytest.raises(SafetyLimitError):
        psu.set_voltage(6)
