import pytest

from itm3900d.parsers import parse_definite_length_block


def test_parse_block():
    assert parse_definite_length_block(b"#15abcde\n") == b"abcde"


def test_parse_bad_block():
    with pytest.raises(ValueError):
        parse_definite_length_block(b"abc")
