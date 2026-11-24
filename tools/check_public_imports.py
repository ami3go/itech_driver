"""Import every installed driver module, including namespace utility modules."""
import importlib
import itech_driver
from pathlib import Path
root = Path(itech_driver.__file__).parent
for file in sorted(root.rglob("*.py")):
    parts = file.relative_to(root).with_suffix("").parts
    name = ".".join(("itech_driver", *parts[:-1])) if parts[-1] == "__init__" else ".".join(("itech_driver", *parts))
    importlib.import_module(name)
    print(name)
