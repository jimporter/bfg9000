# A reference to a macOS framework. Can be used in place of Library objects
# within a Package.


class Framework(object):
    def __init__(self, name, suffix=None):
        self.name = name
        self.suffix = suffix

    @property
    def full_name(self):
        return self.name + ',' + self.suffix if self.suffix else self.name

    def __eq__(self, rhs):
        return (type(self) == type(rhs) and self.name == rhs.name and
                self.suffix == rhs.suffix)

    def __ne__(self, rhs):
        return not (self == rhs)
