from itm3900d.command_catalog import COMMANDS


def test_dangerous_output_command_metadata():
    output_cmds = [c for c in COMMANDS if c.scpi.startswith("OUTPut[:STATe]")]
    assert output_cmds
    assert output_cmds[0].safety_class == "dangerous"
    assert output_cmds[0].requires_confirmation is True
    assert output_cmds[0].requires_output_enable_permission is True


def test_guarded_reset_metadata():
    reset = next(c for c in COMMANDS if c.scpi == "*RST")
    assert reset.safety_class == "guarded"
