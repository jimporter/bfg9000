from collections import OrderedDict

all_targets = OrderedDict()

class Rule(object):
    def __init__(self, kind, name, deps, attrs):
        self.kind = kind
        self.name = name
        self.deps = deps
        self.attrs = attrs

def rule(fn):
    def wrapped(name, deps=None, **kwargs):
        result = Rule(fn.func_name, name, deps or [], fn(**kwargs))
        if name not in all_targets:
            all_targets[name] = []
        all_targets[name].append(result)
        return result
    wrapped.func_name = fn.func_name
    return wrapped

def filter_rules(iterable):
    return filter(lambda i: isinstance(i, Rule), iterable)
