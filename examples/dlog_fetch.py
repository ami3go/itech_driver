from itm3900d import ITM3900D, SafetyPolicy

policy = SafetyPolicy(max_voltage_v=30, max_current_a=5, max_power_w=100)
with ITM3900D.open_usb(safety=policy, allow_output_enable=False) as psu:
    psu.configure_dlog(period=0.1, time_s=5.0, current=True, voltage=True, peak=False)
    psu.start_dlog()
    print("DLOG state:", psu.get_dlog_state())
