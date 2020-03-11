class shell_list(list):
    """A special subclass of list used to mark that this command line uses
    special shell characters."""

    def __repr__(self):
        return '<shell_list({})>'.format(super().__repr__())

    def __add__(self, rhs):
        return shell_list(super().__add__(rhs))

    def __radd__(self, lhs):
        return shell_list(list.__add__(lhs, self))

    def __getitem__(self, key):
        return shell_list(super().__getitem__(key))

    def __eq__(self, rhs):
        return isinstance(rhs, shell_list) and super().__eq__(rhs)

    def __ne__(self, rhs):
        return not self == rhs
