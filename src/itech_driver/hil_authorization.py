"""Local, operator-issued HIL permit. No instrument I/O.

This is a cooperative local gate, not an electrical interlock or an adversarial
security boundary. Protect the encrypted private signing key and PIN from the executing agent.
The runner requires only a trusted operator public key.
"""
import hashlib
import json
import secrets
import time
from pathlib import Path

TTL = 24 * 60 * 60
INTERFACES = {"tcp", "visa-lan", "usbtmc", "vcp"}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read_object(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("expected JSON object")
    return data


def private_write(path, data):
    import os
    path = Path(path)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(canonical(data))


def pin_bytes(pin):
    if not isinstance(pin, str) or not pin.isascii() or not pin.isdecimal() or len(pin) < 6:
        raise ValueError("operator PIN must contain at least six ASCII digits")
    return pin.encode()


def enroll(private_path, authority_path, pin):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    key = Ed25519PrivateKey.generate()
    private_write(private_path, {"encrypted_private_pem": key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(pin_bytes(pin))).decode("ascii")})
    private_write(authority_path, {"public_hex": key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()})


def validate_config(config):
    for name in ("bench_id", "operator", "model", "serial", "firmware", "address",
                 "guide_reference", "safe_state_reference", "emergency_reference"):
        if not isinstance(config.get(name), str) or not config[name].strip():
            raise ValueError("missing bench field: " + name)
    if config.get("interface") not in INTERFACES:
        raise ValueError("invalid interface")
    for name in ("bench_available", "attended", "independent_output_off",
                 "dc_isolated", "emergency_ready"):
        if config.get(name) is not True:
            raise ValueError("unconfirmed prerequisite: " + name)
    if type(config.get("remote_local")) is not bool:
        raise ValueError("remote_local must be boolean")
    if config.get("energized") is not False:
        raise ValueError("energized execution is not implemented by this runner")
    for name, low, high in (("timeout_ms", 1, 10000), ("tcp_port", 1, 65535),
                            ("baudrate", 1, 4_000_000)):
        value = config.get(name)
        if type(value) is not int or not low <= value <= high:
            raise ValueError("invalid explicit transport setting: " + name)
    if type(config.get("bytesize")) is not int or config["bytesize"] not in (5, 6, 7, 8):
        raise ValueError("invalid bytesize")
    if config.get("parity") not in ("N", "E", "O", "M", "S"):
        raise ValueError("invalid parity")
    if type(config.get("stopbits")) is not int or config["stopbits"] not in (1, 2):
        raise ValueError("invalid stopbits")
    if config.get("termination") not in ("lf", "crlf"):
        raise ValueError("invalid termination")
    address = config["address"]
    if config["interface"] == "usbtmc" and not (address.upper().startswith("USB") and address.upper().endswith("::INSTR")):
        raise ValueError("explicit USB INSTR resource required")
    if config["interface"] == "visa-lan" and not (address.upper().startswith("TCPIP") and address.upper().endswith("::INSTR")):
        raise ValueError("explicit TCPIP INSTR resource required")
    if config["interface"] == "vcp" and "://" in address:
        raise ValueError("physical serial device required")
    return config


def digest_config(config):
    return hashlib.sha256(canonical(validate_config(config))).hexdigest()


def issue(private_path, authority_path, config, key_path, pin, now=None):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    key = serialization.load_pem_private_key(
        read_object(private_path)["encrypted_private_pem"].encode("ascii"),
        password=pin_bytes(pin))
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("unexpected private key type")
    public = key.public_key().public_bytes(serialization.Encoding.Raw,
                                           serialization.PublicFormat.Raw).hex()
    if public != read_object(authority_path)["public_hex"]:
        raise ValueError("private/public authority mismatch")
    now = int(time.time() if now is None else now)
    payload = {"version": 1, "id": secrets.token_hex(16), "issued": now,
               "expires": now + TTL, "config_sha256": digest_config(config)}
    private_write(key_path, {"payload": payload, "signature": key.sign(canonical(payload)).hex()})


def validate(authority, config, key_path, now=None):
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    try:
        authority = read_object(authority)
        token = read_object(key_path)
        payload = token["payload"]
        public = Ed25519PublicKey.from_public_bytes(bytes.fromhex(authority["public_hex"]))
        public.verify(bytes.fromhex(token["signature"]), canonical(payload))
        now = time.time() if now is None else now
        issued, expires = payload["issued"], payload["expires"]
        if (payload["version"] != 1 or type(issued) is not int or type(expires) is not int
                or expires - issued != TTL or not issued <= now < expires):
            raise ValueError("expired or invalid validity period")
        if payload["config_sha256"] != digest_config(config):
            raise ValueError("bench scope mismatch")
        return payload["id"]
    except (OSError, KeyError, TypeError, ValueError, AttributeError, InvalidSignature):
        raise ValueError("HIL authorization rejected") from None


def pytest_arguments(config):
    c = validate_config(config)
    args = ["--hil-interface", c["interface"], "--hil-address", c["address"],
            "--hil-serial", c["serial"], "--hil-timeout", str(c["timeout_ms"]),
            "--hil-tcp-port", str(c["tcp_port"]), "--hil-baudrate", str(c["baudrate"]),
            "--hil-bytesize", str(c["bytesize"]), "--hil-parity", c["parity"],
            "--hil-stopbits", str(c["stopbits"]), "--hil-termination", c["termination"]]
    if c["remote_local"]:
        args.append("--hil-remote-local")
    return args


def validate_pytest(config, get):
    mapping = {"interface": "interface", "address": "address", "serial": "serial",
               "timeout": "timeout_ms", "tcp-port": "tcp_port", "baudrate": "baudrate",
               "bytesize": "bytesize", "parity": "parity", "stopbits": "stopbits",
               "termination": "termination", "remote-local": "remote_local"}
    for opt, name in mapping.items():
        if get("--hil-" + opt) != config[name]:
            raise ValueError("pytest endpoint or settings differ from authorized scope")
