import ast
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "example"


@pytest.mark.parametrize("path", sorted(ROOT.glob("*.py")), ids=lambda p: p.name)
def test_examples_compile_and_run_offline(path):
    source = path.read_text(encoding="utf-8")
    compile(source, str(path), "exec")
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            assert not any(a.name.split(".")[0] == "pyvisa" for a in node.names)
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] != "pyvisa"
    subprocess.run([sys.executable, str(path)], check=True, timeout=15)


def test_import_has_no_side_effects():
    subprocess.run([sys.executable, "-c",
                    "import BaseInstrument, advance_use, example3, test, test_import, testw2"],
                   cwd=ROOT, check=True, timeout=15)
