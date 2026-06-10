from itm3900d import ITM3900D


def test_ethernet_resource_generation():
    vxi11, socket = ITM3900D.ethernet_resource_strings("192.168.0.50", 5025)
    assert vxi11 == "TCPIP0::192.168.0.50::inst0::INSTR"
    assert socket == "TCPIP0::192.168.0.50::5025::SOCKET"
