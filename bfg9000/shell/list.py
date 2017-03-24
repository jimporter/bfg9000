class shell_list(list):
    """A special subclass of list used to mark that this command line uses
    special shell characters."""

    def __repr__(self):
        return '<shell_list({})>'.format(list.__repr__(self))

    def __add__(self, rhs):
        return shell_list(list.__add__(self, rhs))

    def __radd__(self, lhs):
        return shell_list(list.__add__(lhs, self))

    def __getitem__(self, key):
        return shell_list(list.__getitem__(self, key))

    def __getslice__(self, i, j):
        return shell_list(list.__getslice__(self, i, j))
