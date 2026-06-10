from itm3900d import ITM3900D
from itm3900d.command_catalog import COMMANDS


def test_format_query_catalog_and_wrapper():
    assert any(cmd.scpi == "FORMat[:data]?" for cmd in COMMANDS)
    psu = ITM3900D(dry_run=True, strict=False)
    psu.open()
    psu.get_format()
    assert "FORM?" in psu.dry_run_writes
