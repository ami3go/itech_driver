import pytest
from scpi_driver_core import ConfigurationError, ResponseParseError
from scpi_driver_core.simulation import ScriptedScpiTransport
from itech_driver import ITM3900D


@pytest.mark.parametrize("api,header,value", [("ip","IP","192.0.2.10"),("subnet","SMAS","255.255.255.0"),("gateway","DGAT","192.0.2.1")])
def test_lan_settings(api, header, value):
    prefix = f"SYST:COMM:LAN:{header}"
    t = ScriptedScpiTransport().on(f'{prefix} "{value}"').on(f"{prefix}?", f'"{value}"')
    with ITM3900D("sim", transport=t) as d:
        getattr(d.system, f"lan_{api}_set")(value)
        assert getattr(d.system, f"lan_{api}_query")() == value
        assert t.history == [f'{prefix} "{value}"', f"{prefix}?"]


@pytest.mark.parametrize("mode,token", [("manual","MAN"),("auto","AUTO")])
def test_separate_mode(mode, token):
    t = ScriptedScpiTransport().on(f"SYST:COMM:LAN:IP:MODE {token}").on("SYST:COMM:LAN:IP:MODE?", token)
    with ITM3900D("sim", transport=t) as d:
        d.system.lan_ip_mode_set(mode)
        assert d.system.lan_ip_mode_query() == token
        assert t.history == [f"SYST:COMM:LAN:IP:MODE {token}", "SYST:COMM:LAN:IP:MODE?"]


def test_invalid_settings_no_io():
    t = ScriptedScpiTransport()
    with ITM3900D("sim", transport=t) as d:
        for value in ("DHCP", "192.0.2.1;*RST", "999.0.0.1", "2001:db8::1", 1):
            with pytest.raises(ConfigurationError):
                d.system.lan_ip_set(value)
        with pytest.raises(ConfigurationError):
            d.system.lan_subnet_set("255.0.255.0")
        with pytest.raises(ConfigurationError):
            d.system.lan_ip_mode_set("DHCP")
        assert t.history == []


def test_malformed_reply():
    t = ScriptedScpiTransport().on("SYST:COMM:LAN:IP?", "garbage")
    with ITM3900D("sim", transport=t) as d, pytest.raises(ResponseParseError):
        d.system.lan_ip_query()
