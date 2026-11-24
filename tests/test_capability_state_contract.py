import pytest
from scpi_driver_core import IdentityError, TransportTimeoutError, UnsupportedOperationError
from scpi_driver_core.simulation import ScriptedScpiTransport
from scpi_driver_core.scpi.parsers import parse_identity
from itech_driver import GenericSCPIInstrument, ITM3900D
from itech_driver.capabilities import CapabilityState, ModelDescriptor, RATINGS, descriptor_for
from itech_driver.exceptions import TimeoutError


@pytest.mark.parametrize("reply", ["42", '-113,"Undefined header"', "timeout"])
def test_speculative_probe_is_not_executed(reply):
    t = ScriptedScpiTransport()
    def respond(_):
        if reply == "timeout":
            raise TransportTimeoutError("query timed out")
        return reply
    t.on("SOUR:VOLT?", respond)
    with GenericSCPIInstrument("sim", transport=t) as d:
        assert d.is_command_supported("SOUR:VOLT?") is None
        assert d.capability_states()["voltage_set"] is CapabilityState.UNKNOWN
        assert d.source is None
        assert t.history == []


def test_explicit_identity_timeout_is_not_unsupported():
    t = ScriptedScpiTransport()
    def fail(_):
        raise TransportTimeoutError("IDN timed out")
    t.on("*IDN?", fail)
    with GenericSCPIInstrument("sim", transport=t) as d:
        with pytest.raises(TimeoutError):
            d.get_instrument_info()
        assert d.capability_states()["output_control"] is CapabilityState.UNKNOWN
        assert t.history == ["*IDN?"]


def test_explicit_malformed_identity_is_not_unsupported():
    t = ScriptedScpiTransport().on("*IDN?", "bad")
    with GenericSCPIInstrument("sim", transport=t) as d:
        with pytest.raises(IdentityError):
            d.get_instrument_info()
        assert d.capability_states()["output_control"] is CapabilityState.UNKNOWN
        assert t.history == ["*IDN?"]


@pytest.mark.parametrize("model", ["IT-M3902D-80-40", "IT-M3906D-1500-12"])
def test_known_descriptor_does_not_promote_unqualified_firmware(model):
    d = descriptor_for(parse_identity(f"ITECH,{model},S,UNKNOWN"))
    assert d.state("identity") is CapabilityState.SUPPORTED
    assert d.state("arb") is CapabilityState.UNQUALIFIED
    assert d.state("unlisted") is CapabilityState.UNKNOWN
    with pytest.raises(UnsupportedOperationError):
        d.require("arb")


def test_explicit_unsupported_is_distinct_from_unknown():
    model = "IT-M3902D-80-40"
    from types import MappingProxyType
    d = ModelDescriptor(model, RATINGS[model], 1, MappingProxyType({
        "identity": CapabilityState.SUPPORTED,
        "synthetic_absent": CapabilityState.UNSUPPORTED,
        "synthetic_unqualified": CapabilityState.UNQUALIFIED,
    }))
    d.require("identity")
    for feature, state in [("synthetic_absent", CapabilityState.UNSUPPORTED),
                           ("synthetic_unqualified", CapabilityState.UNQUALIFIED),
                           ("unlisted", CapabilityState.UNKNOWN)]:
        assert d.state(feature) is state
        with pytest.raises(UnsupportedOperationError, match=state.value):
            d.require(feature)
