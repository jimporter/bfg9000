import importlib
import pkgutil

_builders = {}
_tools = {}
_loaded_tools = False

def _load_tools():
    global _loaded_tools
    if not _loaded_tools:
        # Lazily load the tools so we don't get cyclic imports.
        # XXX: There's probably a better way to do this.
        for _, name, _ in pkgutil.walk_packages(__path__, '.'):
            importlib.import_module(name, __package__)
        _loaded_tools = True

def builder(lang):
    def wrapper(fn):
        _builders[lang] = fn
        return fn
    return wrapper

def get_builder(lang):
    _load_tools()
    try:
        return _builders[lang]
    except KeyError:
        raise ValueError('unknown language "{}"'.format(lang))

def tool(name):
    def wrapper(fn):
        _tools[name] = fn
        return fn
    return wrapper

def get_tool(name):
    _load_tools()
    try:
        return _tools[name]
    except KeyError:
        raise ValueError('unknown tool "{}"'.format(name))
