from enum import EnumMeta as _EnumMeta, Flag as _Flag

from .iterutils import listify as _listify


class _PackageKindMeta(_EnumMeta):
    def __getitem__(cls, name):
        try:
            return _EnumMeta.__getitem__(cls, name)
        except KeyError:
            pass
        raise ValueError('kind must be one of: {}'.format(', '.join(
            "'{}'".format(i.name) for i in cls
        )))


class PackageKind(_Flag, metaclass=_PackageKindMeta):
    static = 1
    shared = 2
    any = static | shared


class Package:
    is_package = True

    def __init__(self, name, submodules=None, *, format, deps=None):
        submodules = _listify(submodules)
        if submodules:
            name = '{}[{}]'.format(name, ','.join(submodules))

        self.name = name
        self.format = format
        self.deps = _listify(deps)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, rhs):
        return (type(self) is type(rhs) and self.name == rhs.name and
                self.format == rhs.format)

    def __ne__(self, rhs):
        return not (self == rhs)

    def __repr__(self):
        return '<{type} {name}>'.format(
            type=type(self).__name__, name=repr(self.name)
        )


class Framework:
    # A reference to a macOS framework. Can be used in place of Library objects
    # within a Package.

    def __init__(self, name, suffix=None):
        self.name = name
        self.suffix = suffix

    @property
    def full_name(self):
        return self.name + ',' + self.suffix if self.suffix else self.name

    def __eq__(self, rhs):
        return (type(self) is type(rhs) and self.name == rhs.name and
                self.suffix == rhs.suffix)

    def __ne__(self, rhs):
        return not (self == rhs)


# TODO: Remove this after 0.8 is released.
class FrameworkPackage(Package):
    def __init__(self, framework, *, format):
        super().__init__(framework.full_name, None, format=format)

        # Import this here to avoid circular import.
        from . import options as opts
        self._compile_options = opts.option_list()
        self._link_options = opts.option_list(opts.framework(framework))

    def compile_options(self, compiler, *, raw=False):
        return self._compile_options

    def link_options(self, linker, *, raw=False):
        return self._link_options
