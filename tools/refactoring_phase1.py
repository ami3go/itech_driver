"""One-time phase-1 reconciliation for the audited integration tree, no HIL."""
import ast
import json
from pathlib import Path

EXPECTED_MISSING = frozenset(["FetchSubsystem.current_array_query","FetchSubsystem.current_binary_array_query","FetchSubsystem.current_high_query","FetchSubsystem.current_low_query","FetchSubsystem.current_max_query","FetchSubsystem.current_min_query","FetchSubsystem.current_query","FetchSubsystem.power_array_query","FetchSubsystem.power_binary_array_query","FetchSubsystem.power_max_query","FetchSubsystem.power_min_query","FetchSubsystem.power_query","FetchSubsystem.voltage_array_query","FetchSubsystem.voltage_binary_array_query","FetchSubsystem.voltage_high_query","FetchSubsystem.voltage_low_query","FetchSubsystem.voltage_max_query","FetchSubsystem.voltage_min_query","FetchSubsystem.voltage_query","IOConfigSubsystem.input_level_query","IOConfigSubsystem.output_level_query","IOConfigSubsystem.output_level_set","IOConfigSubsystem.pin_function_query","IOConfigSubsystem.pin_function_set","IOConfigSubsystem.pulse_width_query","IOConfigSubsystem.pulse_width_set","IOConfigSubsystem.pwm_duty_query","IOConfigSubsystem.pwm_enable_query","IOConfigSubsystem.pwm_freq_query","IOConfigSubsystem.reverse_query","IOConfigSubsystem.reverse_set","IOConfigSubsystem.trigger_source_query","IOConfigSubsystem.trigger_source_set","IOConfigSubsystem.trigger_type_query","IOConfigSubsystem.trigger_type_set","LoggingSubsystem.commands","LoggingSubsystem.raw_data_query","LoggingSubsystem.state_query","MeasurementSubsystem.current_array_query","MeasurementSubsystem.current_binary_array_query","MeasurementSubsystem.current_high_query","MeasurementSubsystem.current_low_query","MeasurementSubsystem.current_max_query","MeasurementSubsystem.current_min_query","MeasurementSubsystem.current_query","MeasurementSubsystem.power_array_query","MeasurementSubsystem.power_binary_array_query","MeasurementSubsystem.power_max_query","MeasurementSubsystem.power_min_query","MeasurementSubsystem.power_query","MeasurementSubsystem.voltage_array_query","MeasurementSubsystem.voltage_binary_array_query","MeasurementSubsystem.voltage_high_query","MeasurementSubsystem.voltage_low_query","MeasurementSubsystem.voltage_max_query","MeasurementSubsystem.voltage_min_query","MeasurementSubsystem.voltage_query","OutputSubsystem.power_on_mode_query","OutputSubsystem.power_on_mode_set","SenseSubsystem.acquisition_interval_query","SenseSubsystem.acquisition_interval_set","SenseSubsystem.acquisition_offset_query","SenseSubsystem.acquisition_offset_set","SenseSubsystem.acquisition_points_query","SenseSubsystem.acquisition_points_set","SourceSubsystem.cc_loop_speed_query","SourceSubsystem.cc_loop_speed_set","SourceSubsystem.current_both_time_query","SourceSubsystem.current_both_time_set","SourceSubsystem.current_fall_time_query","SourceSubsystem.current_fall_time_set","SourceSubsystem.current_limit_query","SourceSubsystem.current_limit_set","SourceSubsystem.current_rise_time_query","SourceSubsystem.current_rise_time_set","SourceSubsystem.cv_loop_speed_query","SourceSubsystem.cv_loop_speed_set","SourceSubsystem.external_coefficient_query","SourceSubsystem.external_coefficient_set","SourceSubsystem.external_programming_query","SourceSubsystem.external_programming_set","SourceSubsystem.ocp_delay_query","SourceSubsystem.ocp_delay_set","SourceSubsystem.opp_delay_query","SourceSubsystem.opp_delay_set","SourceSubsystem.opp_enable","SourceSubsystem.opp_enable_query","SourceSubsystem.opp_threshold_query","SourceSubsystem.opp_threshold_set","SourceSubsystem.output_power_limit_query","SourceSubsystem.output_power_limit_set","SourceSubsystem.ovp_delay_query","SourceSubsystem.ovp_delay_set","SourceSubsystem.programmed_power_limit_query","SourceSubsystem.programmed_power_limit_set","SourceSubsystem.resistance_query","SourceSubsystem.resistance_set","SourceSubsystem.ucp_delay_query","SourceSubsystem.ucp_delay_set","SourceSubsystem.ucp_enable","SourceSubsystem.ucp_enable_query","SourceSubsystem.ucp_query","SourceSubsystem.ucp_set","SourceSubsystem.ucp_warmup_query","SourceSubsystem.ucp_warmup_set","SourceSubsystem.uvp_delay_query","SourceSubsystem.uvp_delay_set","SourceSubsystem.uvp_enable","SourceSubsystem.uvp_enable_query","SourceSubsystem.uvp_query","SourceSubsystem.uvp_set","SourceSubsystem.uvp_warmup_query","SourceSubsystem.uvp_warmup_set","SourceSubsystem.voltage_both_time_query","SourceSubsystem.voltage_both_time_set","SourceSubsystem.voltage_fall_time_query","SourceSubsystem.voltage_fall_time_set","SourceSubsystem.voltage_limit_query","SourceSubsystem.voltage_limit_set","SourceSubsystem.voltage_rise_time_query","SourceSubsystem.voltage_rise_time_set","StatusSubsystem.oper_negative_transition_query","StatusSubsystem.oper_negative_transition_set","StatusSubsystem.oper_positive_transition_query","StatusSubsystem.oper_positive_transition_set","StatusSubsystem.preset","StatusSubsystem.ques_negative_transition_query","StatusSubsystem.ques_negative_transition_set","StatusSubsystem.ques_positive_transition_query","StatusSubsystem.ques_positive_transition_set","SystemSubsystem.lan_ip_mode_query","SystemSubsystem.lan_ip_mode_set","TriggerSubsystem.acquire_arm","TriggerSubsystem.acquire_current_level_query","TriggerSubsystem.acquire_current_level_set","TriggerSubsystem.acquire_source_query","TriggerSubsystem.acquire_source_set","TriggerSubsystem.acquire_voltage_level_query","TriggerSubsystem.acquire_voltage_level_set","TriggerSubsystem.arb_source_query","TriggerSubsystem.arb_source_set","TriggerSubsystem.dlog_source_query","TriggerSubsystem.dlog_source_set","TriggerSubsystem.elog_source_query","TriggerSubsystem.elog_source_set","TriggerSubsystem.hysteresis_threshold_query","TriggerSubsystem.hysteresis_threshold_set"])
def replace_once(path, old, new):
    content = path.read_text(encoding="utf-8")
    if content.count(old) != 1:
        raise RuntimeError(f"Unexpected integration input: {path}: {old!r}")
    path.write_text(content.replace(old, new, 1), encoding="utf-8")

def reconcile(root):
    root = Path(root)
    base = root / "src/itech_driver/base.py"
    model = root / "src/itech_driver/instruments/itm3900d.py"
    source = root / "src/itech_driver/subsystems/SourceSubsystem.py"
    tests = root / "tests/test_remote_mode.py"
    replace_once(base, '    def write_scpi(self, cmd: str) -> None:',
        '    def _assert_write_authorized(self) -> None:\n'
        '        """Policy hook for compound operations; base has no remote policy."""\n'
        '        return None\n\n'
        '    def write_scpi(self, cmd: str) -> None:')
    guard = ('            if self.require_remote and self.requested_mode != "remote":\n'
             '                raise SafetyGuardError("explicit enter_remote() required before writes")')
    replace_once(model, guard, '            self._assert_write_authorized()')
    replace_once(model, '    def write_scpi(self, cmd):',
        '    def _assert_write_authorized(self) -> None:\n'
        '        if self.require_remote and self.requested_mode != "remote":\n'
        '            raise SafetyGuardError("explicit enter_remote() required before writes")\n\n'
        '    def write_scpi(self, cmd):')
    replace_once(source,
        '        with self._p.session.operation_lock():\n            minimum = self._limit_query(header, "MIN")',
        '        with self._p.session.operation_lock():\n'
        '            self._p._assert_write_authorized()\n'
        '            minimum = self._limit_query(header, "MIN")')
    replace_once(tests, '.on("SOUR1:VOLT 1").on("*IDN?",',
        '.on("SOUR:VOLT? MIN", "0").on("SOUR:VOLT? MAX", "10")\n'
        '            .on("SOUR:VOLT 1").on("*IDN?",')
    replace_once(tests, '["*IDN?", "SYST:REM", "SOUR1:VOLT 1", "SYST:LOC"]',
        '["*IDN?", "SYST:REM", "SOUR:VOLT? MIN", "SOUR:VOLT? MAX", "SOUR:VOLT 1", "SYST:LOC"]')
    replace_once(tests, '        d.system.remote()\n        d.ieee.reset()',
        '        assert t.history == ["SYST:REM"]\n'
        '        d.system.remote()\n        d.ieee.reset()')
    replace_once(tests, '        assert d.requested_mode is None\n        with pytest.raises(SafetyGuardError):\n            d.source.voltage_set(1)\n    assert t.history == ["SYST:REM"]',
        '        assert d.requested_mode is None\n'
        '        assert t.state.name == "FAULTED"\n'
        '        with pytest.raises(SafetyGuardError):\n'
        '            d.source.voltage_set(1)\n'
        '        with pytest.raises(SafetyGuardError):\n'
        '            d.output.state_set(True)\n'
        '        assert t.state.name == "FAULTED"\n'
        '        assert t.history == ["SYST:REM"]\n'
        '        d.session.close()\n'
        '        d.session.open()\n'
        '        assert d.requested_mode is None\n'
        '        with pytest.raises(SafetyGuardError):\n'
        '            d.output.state_set(True)\n'
        '    assert t.history == ["SYST:REM"]')
    with tests.open("a", encoding="utf-8") as out:
        out.write('''

def test_missing_range_terminator_invalidates_remote_authorization():
    t = fixture().on("SOUR:VOLT? MIN", b"0")
    with ITM3900D("sim", transport=t, require_remote=True) as d:
        d.enter_remote()
        with pytest.raises(TimeoutError):
            d.source.voltage_set(1)
        assert d.requested_mode is None
        assert t.state.name == "FAULTED"
        with pytest.raises(SafetyGuardError):
            d.output.state_set(True)
        assert t.history == ["SYST:REM", "SOUR:VOLT? MIN"]


def test_fragmented_range_reply_preserves_exact_order():
    t = fixture()
    def fragmented(_):
        t.inner.feed(b"0")
        return b"\\n"
    t.on("SOUR:VOLT? MIN", fragmented)
    with ITM3900D("sim", transport=t, require_remote=True) as d:
        d.enter_remote()
        d.source.voltage_set(1)
    assert t.history == ["SYST:REM", "SOUR:VOLT? MIN", "SOUR:VOLT? MAX", "SOUR:VOLT 1"]
''')
    registry = root / "docs/command_registry.json"
    data = json.loads(registry.read_text(encoding="utf-8"))
    entries = {e["method"]: e for e in data["entries"]}
    if len(entries) != len(data["entries"]):
        raise RuntimeError("Duplicate registry entries")
    inventory = {}
    for path in sorted((root / "src/itech_driver/subsystems").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for cls in ast.parse(text).body:
            if not isinstance(cls, ast.ClassDef):
                continue
            for method in cls.body:
                if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) or method.name.startswith("_"):
                    continue
                key = f"{path.stem}.{method.name}"
                if key in inventory:
                    raise RuntimeError(f"Ambiguous method: {key}")
                inventory[key] = (path, method, text)
    missing = set(inventory) - set(entries)
    extra = set(entries) - set(inventory)
    if missing != EXPECTED_MISSING or extra:
        raise RuntimeError(f"Unexpected registry drift: missing={sorted(missing)} extra={sorted(extra)}")
    for key in sorted(missing):
        path, method, text = inventory[key]
        expressions = [
            ast.get_source_segment(text, node) or ast.unparse(node)
            for node in ast.walk(method)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and (node.func.attr.startswith("_") or node.func.attr.endswith(("_set", "_query"))
                 or node.func.attr in ("write_scpi", "query_scpi", "query_binary"))
        ]
        entries[key] = {
            "method": key, "source": path.relative_to(root).as_posix(),
            "baseline_line": method.lineno, "source_expressions": expressions,
            "guide": {"page": None, "syntax": None, "arguments": None,
                      "response": None, "models": None, "status": "unverified"},
            "retry": "no_automatic_replay", "offline_test": "not_assessed",
            "hil": "not_run", "qualification_note": "Inventory only; guide mapping and capability review pending."
        }
    data["entries"] = list(entries.values())
    data["scope"] = "Public subsystem method inventory at phase-1 integration; not guide or capability qualification."
    registry.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
