"""Opt-in discovery; never issue state-changing commands."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import ipaddress
import threading

from scpi_driver_core import ConfigurationError
from scpi_driver_core.models import Identity

from .identity import is_itm3900d
from .instruments import GenericSCPIInstrument


@dataclass(frozen=True)
class Endpoint:
    interface: str
    address: str
    port: int | None = None


@dataclass(frozen=True)
class DiscoveredInstrument:
    identity: Identity
    endpoints: tuple[Endpoint, ...]


@dataclass(frozen=True)
class DiscoveryReport:
    devices: tuple[DiscoveredInstrument, ...]
    diagnostics: tuple[str, ...]


def _visa_candidates():
    import pyvisa
    # ResourceManager may be shared; do not close it here.
    # PyVISA caches a process-shared manager; closing it can invalidate other drivers.
    resources = pyvisa.ResourceManager().list_resources()
    return [Endpoint("usbtmc" if r.upper().startswith("USB") else "visa-lan", r)
            for r in resources
            if r.upper().startswith(("USB", "TCPIP")) and r.upper().endswith(("::INSTR", "::SOCKET"))]


def _mdns_candidates():
    from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
    types = ["_vxi-11._tcp.local.", "_scpi-raw._tcp.local."]
    names = set()
    lock = threading.Lock()
    class Listener(ServiceListener):
        def add_service(self, zc, type_, name):
            with lock:
                if len(names) < 32:
                    names.add((type_, name))
        def update_service(self, zc, type_, name):
            self.add_service(zc, type_, name)
        def remove_service(self, zc, type_, name):
            with lock:
                names.discard((type_, name))
    zc = Zeroconf()
    browser = None
    try:
        browser = ServiceBrowser(zc, types, Listener())
        threading.Event().wait(1)
        with lock:
            found = sorted(names)
        endpoints = []
        for type_, name in found:
            info = zc.get_service_info(type_, name, timeout=200)
            if info is None:
                continue
            for address in info.parsed_addresses():
                if ":" in address:  # IPv4 discovery only for now
                    continue
                if type_ == types[0]:
                    endpoints.append(Endpoint("visa-lan", f"TCPIP0::{address}::inst0::INSTR"))
                else:
                    endpoints.append(Endpoint("tcp", address, info.port))
        return endpoints
    finally:
        try:
            if browser is not None:
                browser.cancel()
        finally:
            zc.close()


def _vcp_candidates():
    from serial.tools.list_ports import comports
    return [Endpoint("vcp", p.device) for p in comports() if p.vid is not None]


def _subnet_candidates(subnet, port):
    if subnet is None:
        return []
    try:
        network = ipaddress.ip_network(subnet, strict=False)
    except ValueError as exc:
        raise ConfigurationError("invalid discovery subnet") from exc
    allowed = [ipaddress.ip_network(c) for c in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "169.254.0.0/16")]
    if network.version != 4 or network.num_addresses > 256 or not any(network.subnet_of(n) for n in allowed):
        raise ConfigurationError("use an explicitly selected private IPv4 subnet with at most 256 addresses")
    return [Endpoint("tcp", str(host), port) for host in network.hosts()]


def _probe(endpoint, timeout, baudrate):
    from .connection import ConnectionConfig
    if endpoint.interface == "tcp":
        host = endpoint.address
        authority = f"[{host}]" if ":" in host else host
        config = ConnectionConfig(f"tcp://{authority}:{endpoint.port}", timeout_ms=timeout)
    elif endpoint.interface == "vcp":
        config = ConnectionConfig(f"vcp:{endpoint.address}", timeout_ms=timeout, baudrate=baudrate)
    else:
        config = ConnectionConfig(endpoint.address, timeout_ms=timeout, interface="visa")
    with GenericSCPIInstrument(config.resource, connection=config) as driver:
        return driver.identity_snapshot()


def discover_instruments(*, subnet=None, port=30000, timeout=1000, probe_vcp=False,
                         baudrate=9600, use_visa=True, use_mdns=True, workers=8):
    """Find devices by explicit invocation; optional backend failures are reported."""
    if any(type(flag) is not bool for flag in (probe_vcp, use_visa, use_mdns)):
        raise ConfigurationError("discovery provider flags must be bool")
    if type(timeout) is not int or not 1 <= timeout <= 10000:
        raise ConfigurationError("discovery timeout must be 1..10000 ms")
    if type(port) is not int or not 1 <= port <= 65535:
        raise ConfigurationError("invalid TCP port")
    if type(workers) is not int or not 1 <= workers <= 16:
        raise ConfigurationError("workers must be 1..16")
    if type(baudrate) is not int or baudrate <= 0:
        raise ConfigurationError("invalid baudrate")
    candidates = _subnet_candidates(subnet, port)
    diagnostics = []
    for enabled, name, enumerate_ in ((use_visa, "VISA", _visa_candidates),
                                      (use_mdns, "mDNS", _mdns_candidates),
                                      (probe_vcp, "VCP", _vcp_candidates)):
        if enabled:
            try:
                candidates.extend(enumerate_())
            except Exception as exc:
                diagnostics.append(f"{name} enumeration: {exc}")
    candidates = list(dict.fromkeys(candidates))
    if len(candidates) > 320:
        raise ConfigurationError("too many discovery candidates; narrow the search")
    def attempt(endpoint):
        try:
            identity = _probe(endpoint, timeout, baudrate)
            if not is_itm3900d(identity):
                return endpoint, None, "not an IT-M3900D identity"
            return endpoint, identity, None
        except Exception as exc:
            return endpoint, None, str(exc)
    grouped = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for endpoint, identity, error in pool.map(attempt, candidates):
            if error is not None:
                diagnostics.append(f"{endpoint.interface} {endpoint.address}: {error}")
                continue
            serial = (identity.serial_number or "").strip().upper()
            key = (identity.model.strip().upper(), serial) if serial and serial not in ("0", "N/A", "UNKNOWN") else endpoint
            if key not in grouped:
                grouped[key] = (identity, [])
            grouped[key][1].append(endpoint)
    return DiscoveryReport(tuple(DiscoveredInstrument(i, tuple(e)) for i, e in grouped.values()),
                           tuple(diagnostics))
