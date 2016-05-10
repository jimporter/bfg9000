import os.path
import re
from packaging.version import Version
import subprocess

from .hooks import builtin
from .find import find
from .version import check_version, make_specifier
from .. import shell
from ..file_types import Executable
from ..iterutils import iterate, listify
from ..path import Path, Root
from ..platforms import which


class Package(object):
    pass


class SystemPackage(Package):
    def __init__(self, includes=None, lib_dirs=None, libraries=None,
                 version=None):
        self._includes = includes or []
        self._lib_dirs = lib_dirs or []
        self._libraries = libraries or []
        self.version = version

    def cflags(self, builder, output):
        return builder.args(self._includes)

    def ldflags(self, builder, output):
        return builder.pkg_args(self._libraries, output, self._lib_dirs)

    def ldlibs(self, builder, output):
        return builder.libs(self._libraries)


class PkgConfigPackage(Package):
    def __init__(self, name, pkg_config):
        self.name = name
        self._pkg_config = pkg_config

    def _call(self, command, *args):
        return subprocess.check_output(
            getattr(self._pkg_config, command)(
                self._pkg_config.command, self.name, *args
            ), universal_newlines=True
        ).strip()

    @property
    def version(self):
        # XXX: This should probably be a LegacyVersion, but that would make it
        # a lot harder to work with SpecifierSets.
        return Version(self._call('version'))

    def cflags(self, builder, output):
        return shell.split(self._call('cflags', builder.flavor == 'msvc'))

    def ldflags(self, builder, output):
        return shell.split(self._call('ldflags', builder.flavor == 'msvc'))

    def ldlibs(self, builder, output):
        return shell.split(self._call('ldlibs', builder.flavor == 'msvc'))


def _boost_version(header, required_version=None):
    version_hpp = header.path.append('boost').append('version.hpp')
    with open(version_hpp.string()) as f:
        for line in f:
            m = re.match(r'#\s*define\s+BOOST_LIB_VERSION\s+"([\d_]+)"', line)
            if m:
                version = Version(m.group(1).replace('_', '.'))
                check_version(version, required_version, 'Boost')
                return version
    raise IOError('unable to parse "boost/version.hpp"')


@builtin.globals('env')
def system_package(env, name, lang='c', kind='any'):
    if kind not in ('any', 'shared', 'static'):
        raise ValueError("kind must be one of 'any', 'shared', or 'static'")
    lib = env.builder(lang).packages.library(name, kind)
    return SystemPackage(libraries=[lib])


@builtin.globals('env')
def boost_package(env, name=None, version=None):
    version = make_specifier(version)
    pkg = env.builder('c++').packages
    version_hpp = os.path.join('boost', 'version.hpp')

    root = env.getvar('BOOST_ROOT')
    incdir = env.getvar('BOOST_INCLUDEDIR', os.path.join(root, 'include')
                        if root else None)
    libdir = env.getvar('BOOST_LIBRARYDIR', os.path.join(root, 'lib')
                        if root else None)

    if incdir:
        header = pkg.header(version_hpp, [incdir])
        boost_version = _boost_version(header, version)
    else:
        # On Windows, check the default install location, which is structured
        # differently from other install locations.
        if env.platform.name == 'windows':
            dirs = find(r'C:\Boost\include', 'boost-*', type='d', flat=True)
            if dirs:
                try:
                    header = pkg.header(version_hpp, [max(dirs)])
                    boost_version = _boost_version(header, version)
                    return SystemPackage(
                        includes=[header],
                        lib_dirs=[r'C:\Boost\lib'],
                        version=boost_version
                    )
                except IOError:
                    pass

        header = pkg.header(version_hpp)
        boost_version = _boost_version(header, version)

    if env.platform.name == 'windows':
        if not env.builder('c++').auto_link:
            # XXX: Don't require auto-link.
            raise ValueError('Boost on Windows requires auto-link')
        return SystemPackage(
            includes=[header],
            lib_dirs=listify(libdir),
            version=boost_version
        )
    else:
        dirs = [libdir] if libdir else None
        return SystemPackage(
            includes=[header],
            libraries=[pkg.library('boost_' + i, search_dirs=dirs)
                       for i in iterate(name)],
            version=boost_version
        )


@builtin.globals('env')
def pkgconfig_package(env, name, version=None):
    pkg = PkgConfigPackage(name, env.tool('pkg_config'))
    version = make_specifier(version)
    check_version(pkg.version, version, name)
    return pkg


@builtin.globals('env')
def system_executable(env, name, format=None):
    return Executable(Path(which(name, env.variables), Root.absolute),
                      format or env.platform.object_format, external=True)
