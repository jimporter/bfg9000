from collections import OrderedDict
from pkg_resources import iter_entry_points, DistributionNotFound


def get_backends():
    backends = []
    for i in iter_entry_points('bfg9000.backends'):
        try:
            backend = i.load()
            backends.append((i.name, backend))
        except DistributionNotFound:
            pass

    def sort_key(x):
        return x[1].priority if x[1].version() else 0
    backends.sort(key=sort_key, reverse=True)
    return OrderedDict(backends)
