"""Read-only measurement example; offline simulation unless --resource is supplied."""
import argparse
from itech_driver import ITM3900D, auto_detect_instrument
from itech_driver.simulator import ItechSimulator


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resource", help="Explicit resource for read-only measurements")
    args = p.parse_args(argv)
    driver = (auto_detect_instrument(args.resource) if args.resource is not None
              else ITM3900D("sim", transport=ItechSimulator().transport))
    with driver:
        print(driver.identify())
        if isinstance(driver, ITM3900D):
            print("Voltage:", driver.measurement.voltage_query())
            print("Current:", driver.measurement.current_query())
            print("Output setting:", driver.output.state_query())


if __name__ == "__main__":
    main()
