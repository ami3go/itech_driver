from itm3900d.parsers import parse_scpi_error


def test_parse_no_error():
    rec = parse_scpi_error('+0,"No error"')
    assert rec.code == 0
    assert rec.is_no_error


def test_parse_command_error():
    rec = parse_scpi_error('-113,"Undefined header"')
    assert rec.code == -113
    assert rec.message == "Undefined header"
