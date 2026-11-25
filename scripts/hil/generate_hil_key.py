"""Interactive operator tool. Keep authority and key outside the repository."""
import argparse
from getpass import getpass
from pathlib import Path
from itech_driver.hil_authorization import enroll, issue, read_object

ROOT = Path(__file__).resolve().parents[2]


def external(path):
    p = Path(path).resolve()
    if p.is_relative_to(ROOT):
        raise ValueError("keep authority and authorization key outside the repository")
    return p


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--authority", required=True, help="trusted public key")
    p.add_argument("--private", required=True, help="operator-only encrypted signing key")
    p.add_argument("--enroll", action="store_true")
    p.add_argument("--config")
    p.add_argument("--key")
    a = p.parse_args()
    try:
        authority = external(a.authority)
        private = external(a.private)
        if private == authority:
            raise ValueError("separate public and private paths required")
        if a.enroll:
            pin = getpass("New operator PIN: ")
            if pin != getpass("Repeat operator PIN: "):
                raise ValueError("PIN mismatch")
            enroll(private, authority, pin)
        else:
            if not a.config or not a.key:
                p.error("--config and --key required")
            config = read_object(a.config)
            if input("Confirm attended, independently isolated bench and scope [YES]: ") != "YES":
                raise ValueError("operator declined")
            issue(private, authority, config, external(a.key), getpass("Operator PIN: "))
        print("Local authorization operation completed; do not commit private key or permit.")
    except (ValueError, OSError, KeyError):
        p.exit(2, "Authorization operation rejected; verify local files and operator approval.\n")


if __name__ == "__main__":
    main()
