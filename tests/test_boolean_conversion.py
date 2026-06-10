import pytest

from itm3900d.parsers import from_bool_response, to_bool


def test_to_bool():
    assert to_bool(True) == "ON"
    assert to_bool(False) == "OFF"
    assert to_bool("1") == "ON"
    assert to_bool("off") == "OFF"


def test_bool_bad():
    with pytest.raises(ValueError):
        to_bool("maybe")


def test_from_bool_response():
    assert from_bool_response("1") is True
    assert from_bool_response("0") is False
