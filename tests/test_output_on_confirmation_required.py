import pytest

from itm3900d import ITM3900D, SafetyPolicy
from itm3900d.exceptions import OutputEnableConfirmationRequired


def test_raw_output_on_requires_confirmation():
    psu = ITM3900D(dry_run=True, strict=False, safety=SafetyPolicy(max_voltage_v=5, max_current_a=1), allow_output_enable=True)
    psu.open()
    psu.configure_cv(1, 0.1)
    psu.dry_run = False
    with pytest.raises(OutputEnableConfirmationRequired):
        psu.write("OUTP ON")
