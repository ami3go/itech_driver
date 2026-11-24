"""Factory demonstration; simulator by default, explicit resource for read-only hardware."""
import argparse
from itech_driver import auto_detect_instrument, create_instrument, list_available_instruments
from itech_driver.simulator import ItechSimulator


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource", help="Explicit hardware resource; identity only")
    args = parser.parse_args(argv)
    print("Supported factory names:", list_available_instruments())
    if args.resource is not None:
        with auto_detect_instrument(args.resource) as driver:
            print(driver.identity_snapshot().raw)
        return
    with create_instrument("IT-M3900D", "sim", transport=ItechSimulator().transport) as driver:
        print(driver.identify())
        print("Measured voltage:", driver.measurement.voltage_query())


if __name__ == "__main__":
    main()
