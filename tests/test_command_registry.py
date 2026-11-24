"""Registry completeness for existing subsystem methods; no hardware access."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "command_registry.json"


def test_subsystem_registry_covers_public_methods():
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    entries = data["entries"]
    actual = set()
    for path in (ROOT / "src/itech_driver/subsystems").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for cls in (node for node in tree.body if isinstance(node, ast.ClassDef)):
            actual.update(f"{path.stem}.{node.name}" for node in cls.body
                          if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                          and not node.name.startswith("_"))
    registered = [entry["method"] for entry in entries]
    assert len(registered) == len(set(registered)), "duplicate command registry entry"
    assert set(registered) == actual
    for entry in entries:
        assert (ROOT / entry["source"]).is_file()
        assert entry["guide"]["status"] in {"unverified", "indexed_text_reference", "guide_verified"}
        if entry["guide"]["status"] == "guide_verified":
            assert data["reference"]["revision"] != "unconfirmed"
            assert entry["guide"]["page"] and entry["guide"]["syntax"]
        assert entry["hil"] in {"not_run", "passed", "failed"}


def test_integrated_new_public_methods_and_aliases_have_explicit_registry_entries():
    entries = {e["method"]: e for e in json.loads(REGISTRY.read_text(encoding="utf-8"))["entries"]}
    # Previously omitted methods spanning independent subsystem implementations.
    for name in (
        "SourceSubsystem.voltage_both_time_query",
        "IOConfigSubsystem.input_level_query",
        "MeasurementSubsystem.voltage_min_query",
        "FetchSubsystem.power_binary_array_query",
        "TriggerSubsystem.hysteresis_threshold_set",
        "LoggingSubsystem.commands",
    ):
        assert name in entries
        assert entries[name]["guide"]["status"] == "unverified"
        assert entries[name]["retry"] == "no_automatic_replay"
    for name, target in {"SourceSubsystem.transient_mode_set":"SourceSubsystem.function_mode_set","SourceSubsystem.transient_mode_query":"SourceSubsystem.function_mode_query","SourceSubsystem.power_limit_set":"SourceSubsystem.opp_threshold_set","SourceSubsystem.power_limit_query":"SourceSubsystem.opp_threshold_query","SourceSubsystem.power_limit_enable":"SourceSubsystem.opp_enable","SourceSubsystem.power_limit_enable_query":"SourceSubsystem.opp_enable_query"}.items():
        assert entries[name]["alias_of"] == target
        assert target in entries
    assert entries["SourceSubsystem.remote_sense_query"]["implementation_status"] == "restricted_unqualified"
