import functools

_all_builtins = {}

def builtin(fn):
    _all_builtins[fn.__name__] = fn
    return fn

def bind(build_inputs):
    result = {}
    for k, v in _all_builtins.iteritems():
        result[k] = functools.partial(v, build_inputs)
    return result
