from enum import EnumMeta as _EnumMeta, Flag as _Flag

from .iterutils import listify as _listify
from .options import option_list as _option_list
from .platforms.framework import Framework  # noqa


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

    def __init__(self, name, format, deps=None):
        self.name = name
        self.format = format
        self.deps = _listify(deps)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, rhs):
        return (type(self) == type(rhs) and self.name == rhs.name and
                self.format == rhs.format)

    def __ne__(self, rhs):
        return not (self == rhs)

    def __repr__(self):
        return '<{type} {name}>'.format(
            type=type(self).__name__, name=repr(self.name)
        )


class CommonPackage(Package):
    def __init__(self, name, format, compile_options=None, link_options=None):
        super().__init__(name, format)
        self._compile_options = compile_options or _option_list()
        self._link_options = link_options or _option_list()

    def compile_options(self, compiler):
        return self._compile_options

    def link_options(self, linker):
        return self._link_options
