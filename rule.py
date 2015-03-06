all_targets = []

class Rule(object):
    def __init__(self, kind, name, deps, attrs):
        self.kind = kind
        self.name = name
        self.deps = deps
        self._attrs = attrs

    def __getitem__(self, key):
        return self._attrs[key]

    def __contains__(self, key):
        return key in self._attrs[key]

def rule(fn):
    def wrapped(name, deps=None, **kwargs):
        result = Rule(fn.func_name, name, deps or [], fn(**kwargs))
        all_targets.append(result)
        return result
    wrapped.func_name = fn.func_name
    return wrapped

def filter_rules(iterable):
    return filter(lambda i: isinstance(i, Rule), iterable)
