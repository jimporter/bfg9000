all_builtins = {}

def builtin(fn):
    all_builtins[fn.__name__] = fn
    return fn
