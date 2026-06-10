from itm3900d import ITM3900D, SafetyPolicy

policy = SafetyPolicy(max_voltage_v=30, max_current_a=5, max_power_w=100)
with ITM3900D.open_usb(safety=policy, allow_output_enable=False) as psu:
    psu.configure_elog(period=0.001, time_s=1.0)
    psu.start_elog()
    raw = psu.fetch_elog_array_data_raw()
    print(f"Read {len(raw)} raw bytes")
