import pytest
from scpi_driver_core import ConfigurationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("kwargs", [
    {}, {"storage_confirmed":True}, {"storage_confirmed":True,"seconds_since_previous_end":4.9},
    {"storage_confirmed":True,"seconds_since_previous_end":float("inf")},
    {"storage_confirmed":True,"seconds_since_previous_end":float("nan")},
    {"storage_confirmed":False,"no_previous_recording_confirmed":True},
    {"storage_confirmed":True,"no_previous_recording_confirmed":True,"seconds_since_previous_end":5},
])
def test_missing_or_invalid_prerequisites_send_nothing(kwargs):
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        with pytest.raises(ConfigurationError):
            d.initiate.dlog(**kwargs)
        assert t.history == []


@pytest.mark.parametrize("kwargs", [
    {"storage_confirmed":True,"no_previous_recording_confirmed":True},
    {"storage_confirmed":True,"seconds_since_previous_end":5},
])
def test_explicit_prerequisite_attestation(kwargs):
    t = ScriptedScpiTransport().on("INITiate:DLOG")
    with ITM3900D("sim", transport=t) as d:
        d.initiate.dlog(**kwargs)
        assert t.history == ["INITiate:DLOG"]
