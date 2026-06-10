from itm3900d.command_catalog import COMMANDS


def test_output_queries_present():
    scpi = {cmd.scpi for cmd in COMMANDS}
    assert "OUTPut:INHibit:MODE?" in scpi
    assert "OUTPut:PON:STATe?" in scpi
    assert "OUTPut:PROTection:WDOG[:STATe]?" in scpi
    assert "OUTPut:PROTection:WDOG:DELay? [MINimum|MAXimum|DEFault]" in scpi
