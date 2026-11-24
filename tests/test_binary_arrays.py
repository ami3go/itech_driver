import struct
import pytest
from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("api,prefix", [("measurement","MEAS"),("fetch","FETC")])
@pytest.mark.parametrize("quantity,header", [("voltage","VOLT"),("current","CURR"),("power","POW")])
@pytest.mark.parametrize("order,endian", [("little","<"),("big",">")])
@pytest.mark.parametrize("datatype", ["f","d"])
def test_explicit_binary_decode(api,prefix,quantity,header,order,endian,datatype):
    cmd = f"{prefix}:ARR:{header}?"
    t = ScriptedScpiTransport().reply_block(cmd,struct.pack(endian+"2"+datatype,1.25,2.5))
    with ITM3900D("sim",transport=t) as d:
        query = getattr(getattr(d,api),quantity+"_binary_array_query")
        assert query(datatype=datatype,byte_order=order,expected_points=2,
                     binary_confirmed=True,consume_terminator=True) == [1.25,2.5]
        assert t.history == [cmd]


def test_unknown_binary_format_no_io():
    t = ScriptedScpiTransport()
    with ITM3900D("sim",transport=t) as d:
        with pytest.raises(ConfigurationError):
            d.fetch.voltage_binary_array_query(datatype="f",byte_order="little",
                expected_points=2,consume_terminator=True)
        assert t.history == []


@pytest.mark.parametrize("payload", [b"abc", struct.pack("<f",1), struct.pack("<2f",1,float("nan"))])
def test_malformed_binary(payload):
    t = ScriptedScpiTransport().reply_block("FETC:ARR:VOLT?",payload)
    with ITM3900D("sim",transport=t) as d, pytest.raises(ResponseParseError):
        d.fetch.voltage_binary_array_query(datatype="f",byte_order="little",
            expected_points=2,binary_confirmed=True,consume_terminator=True)
