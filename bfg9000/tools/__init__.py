import importlib
import pkgutil

from .hooks import get_builder, get_tool  # noqa

# Import all the packages in this directory so their hooks get run.
for _, name, _ in pkgutil.walk_packages(__path__, '.'):
    importlib.import_module(name, __package__)
