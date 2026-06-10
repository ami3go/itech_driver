from itm3900d import ITM3900D, SafetyPolicy

policy = SafetyPolicy(max_voltage_v=30, max_current_a=5, max_power_w=100)
with ITM3900D.open_usb(safety=policy, allow_output_enable=False) as psu:
    psu.io_select(1)
    psu.set_io_direction(1, True)
    psu.set_io_output_level(1, "HIGH")
    print(psu.get_io_input_level(1))
