import importlib
import pkgutil

from ..file_types import Executable
from ..objutils import memoize

_builders = {}
_tools = {}
_tool_runners = {}


@memoize
def init():
    # Import all the packages in this directory so their hooks get run.
    for _, name, _ in pkgutil.walk_packages(__path__, '.'):
        importlib.import_module(name, __package__)


def builder(*args):
    if len(args) == 0:
        raise TypeError('must provide at least one language')
    multi = len(args) > 1

    def wrapper(fn):
        for i in args:
            _builders[i] = (fn, multi)
        return fn
    return wrapper


def get_builder(env, lang):
    try:
        fn, multi = _builders[lang]
        return fn(env, lang) if multi else fn(env)
    except KeyError:
        raise ValueError("unknown language '{}'".format(lang))


def tool(name, lang=None):
    def wrapper(fn):
        _tools[name] = fn
        if lang:
            _tool_runners[lang] = name
        return fn
    return wrapper


def get_tool(env, name):
    try:
        return _tools[name](env)
    except KeyError:
        raise ValueError("unknown tool '{}'".format(name))


def get_tool_runner(lang):
    try:
        return _tool_runners[lang]
    except KeyError:
        raise ValueError("unknown tool runner '{}'".format(lang))
