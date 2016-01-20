_builders = {}
_tools = {}


def builder(*args):
    if len(args) == 0:
        raise TypeError('must provide at least one language')
    multi = len(args) > 1

    def wrapper(fn):
        for i in args:
            _builders[i] = (fn, multi)
        return fn
    return wrapper


def get_builder(lang, env):
    try:
        fn, multi = _builders[lang]
        return fn(env, lang) if multi else fn(env)
    except KeyError:
        raise ValueError('unknown language "{}"'.format(lang))


def tool(name):
    def wrapper(fn):
        _tools[name] = fn
        return fn
    return wrapper


def get_tool(name, env):
    try:
        return _tools[name](env)
    except KeyError:
        raise ValueError('unknown tool "{}"'.format(name))
