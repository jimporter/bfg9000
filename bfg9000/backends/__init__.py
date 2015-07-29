from pkg_resources import iter_entry_points, DistributionNotFound

def get_backends():
    backends = {}
    default_backend = None
    top_priority = -1

    for i in iter_entry_points('bfg9000.backends'):
        try:
            backend = i.load()
            if backend.priority == -1:
                continue
            if backend.priority > top_priority:
                default_backend = i.name
                top_priority = backend.priority
            backends[i.name] = backend
        except DistributionNotFound:
            pass

    return backends, default_backend

