import importlib
import pkgutil
import sys

from . import builtin
from .. import exceptions
from ..objutils import memoize


@memoize
def init():
    # Import all the packages in this directory so their hooks get run.
    for _, name, _ in pkgutil.walk_packages(__path__, '.'):
        importlib.import_module(name, __package__)


@builtin.getter('env', context='*')
def env(_env):
    return _env


for i in dir(exceptions):
    i = getattr(exceptions, i)
    if isinstance(i, type):
        builtin.function(i, context='*')
