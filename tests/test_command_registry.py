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
