"""Verify the installed factory import aliases."""
from itech_driver import auto_detect_instrument
from itech_driver.instruments import auto_detect_instrument as direct


def main():
    assert auto_detect_instrument is direct
    print("Factory imports match")


if __name__ == "__main__":
    main()
