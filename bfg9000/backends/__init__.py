from collections import OrderedDict
from pkg_resources import iter_entry_points, DistributionNotFound

def get_backends():
    backends = []
    for i in iter_entry_points('bfg9000.backends'):
        try:
            backend = i.load()
            if backend.priority >= 0:
                backends.append((i.name, backend))
        except DistributionNotFound:
            pass

    backends.sort(key=lambda x: x[1].priority, reverse=True)
    return OrderedDict(backends)
