import importlib
import pkgutil
import warnings

from . import builtin
from .. import exceptions
from .. import log
from ..objutils import memoize


@memoize
def init():
    # Import all the packages in this directory so their hooks get run.
    for _, name, _ in pkgutil.walk_packages(__path__, '.'):
        importlib.import_module(name, __package__)


@builtin.getter('env', name='env', context=('build', 'options'))
def getenv(env):
    return env


@builtin.function(context='*')
def warning(msg):
    warnings.warn(msg)


@builtin.function(context='*')
def info(msg, show_stack=False):
    log.log_stack(log.INFO, msg, show_stack=show_stack, stacklevel=1)


@builtin.function(context='*')
def debug(msg, show_stack=True):
    log.log_stack(log.DEBUG, msg, show_stack=show_stack, stacklevel=1)


for i in dir(exceptions):
    i = getattr(exceptions, i)
    if isinstance(i, type):
        builtin.function(context='*')(i)
