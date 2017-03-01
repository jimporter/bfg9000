import importlib
import pkgutil

from ..file_types import Executable

_builders = {}
_tools = {}
_runners = {}
_initialized = False


def init():
    global _initialized
    if _initialized:
        return
    _initialized = True

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


def tool(name):
    def wrapper(fn):
        _tools[name] = fn
        return fn
    return wrapper


def get_tool(env, name):
    try:
        return _tools[name](env)
    except KeyError:
        raise ValueError("unknown tool '{}'".format(name))


def runner(*args):
    if len(args) == 0:
        raise TypeError('must provide at least one language')
    multi = len(args) > 1

    def wrapper(fn):
        for i in args:
            _runners[i] = (fn, multi)
        return fn
    return wrapper


def get_run_arguments(env, lang, file):
    if lang in _runners:
        fn, multi = _runners[lang]
        args = fn(env, lang, file) if multi else fn(env, file)
        if args is not None:
            return args

    if not isinstance(file, Executable):
        raise TypeError('expected an executable for {} to run'
                        .format(lang))
    return [file]
