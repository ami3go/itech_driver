"""Hardware-in-loop placeholder.

Edit IP/resource and safety limits before running. Every script must require
operator confirmation before output ON.
"""

from itm3900d import ITM3900D, SafetyPolicy


def main() -> None:
    policy = SafetyPolicy(max_voltage_v=5, max_current_a=0.5, max_power_w=3)
    # Change this to open_ethernet(...) for Ethernet scripts.
    psu = ITM3900D.open_usb(safety=policy, allow_output_enable=True)
    try:
        print(psu.idn())
        psu.configure_cv(1.0, 0.1, 1.0)
        if input("Type ENABLE to turn output ON: ") == "ENABLE":
            psu.output_on(confirm=True)
        print(psu.measure_scalar())
    finally:
        psu.output_off(verify=True)
        psu.close()


if __name__ == "__main__":
    main()
