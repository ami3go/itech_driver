from itm3900d.command_catalog import COMMANDS, COMMANDS_BY_KEY


def test_catalog_is_large_and_unique():
    assert len(COMMANDS) >= 330
    assert len(COMMANDS_BY_KEY) == len(COMMANDS)


def test_format_query_present():
    assert any(cmd.scpi == "FORMat[:data]?" for cmd in COMMANDS)
