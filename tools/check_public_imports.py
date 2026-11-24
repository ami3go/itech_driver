"""Import every installed driver module without discovery or device access."""
import importlib
import pkgutil
import itech_driver

for module in pkgutil.walk_packages(itech_driver.__path__, itech_driver.__name__ + "."):
    importlib.import_module(module.name)
    print(module.name)
