all_builtins = {}

def builtin(fn):
    all_builtins[fn.func_name] = fn
    return fn
