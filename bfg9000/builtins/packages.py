import os.path
import re

from . import builtin
from .find import find
from .. import options as opts
from ..exceptions import PackageResolutionError, PackageVersionError
from ..file_types import Directory, Executable
from ..iterutils import default_sentinel, iterate
from ..objutils import objectify
from ..packages import CommonPackage, Framework, Package, PackageKind
from ..path import Path, Root
from ..shell import which
from ..versioning import check_version, SpecifierSet, Version


class BoostPackage(CommonPackage):
    def __init__(self, name, format, version, *args, **kwargs):
        name = 'boost({})'.format(','.join(iterate(name)))
        CommonPackage.__init__(self, name, format, *args, **kwargs)
        self.version = version


@builtin.function('env')
@builtin.type(Package)
def package(env, name, version=None, lang='c', kind=PackageKind.any.name,
            headers=None, libs=default_sentinel):
    version = objectify(version or '', SpecifierSet)
    kind = PackageKind[kind]
    return env.builder(lang).packages.resolve(name, version, kind, headers,
                                              libs)


@builtin.function('env')
@builtin.type(Executable)
def system_executable(env, name, format=None):
    return Executable(
        Path(which([[name]], env.variables, resolve=True)[0], Root.absolute),
        format or env.target_platform.object_format, external=True
    )


@builtin.function('env')
def framework(env, name, suffix=None):
    if not env.target_platform.has_frameworks:
        raise PackageResolutionError("{} platform doesn't support frameworks"
                                     .format(env.target_platform.name))

    framework = Framework(name, suffix)
    return CommonPackage(framework.full_name,
                         env.target_platform.object_format,
                         link_options=opts.option_list(opts.lib(framework)))


def _boost_version(header, required_version):
    version_hpp = header.path.append('boost').append('version.hpp')
    with open(version_hpp.string()) as f:
        for line in f:
            m = re.match(r'#\s*define\s+BOOST_LIB_VERSION\s+"([\d_]+)"', line)
            if m:
                version = Version(m.group(1).replace('_', '.'))
                check_version(version, required_version, 'boost',
                              PackageVersionError)
                return version
    raise PackageVersionError('unable to parse "boost/version.hpp"')


@builtin.function('env')
def boost_package(env, name=None, version=None):
    version = objectify(version or '', SpecifierSet)
    pkg = env.builder('c++').packages
    version_hpp = 'boost/version.hpp'

    root = env.getvar('BOOST_ROOT')
    incdir = env.getvar('BOOST_INCLUDEDIR', os.path.join(root, 'include')
                        if root else None)
    libdir = env.getvar('BOOST_LIBRARYDIR', os.path.join(root, 'lib')
                        if root else None)
    header = None

    if env.target_platform.family == 'windows':
        if not env.builder('c++').auto_link:  # pragma: no cover
            # XXX: Don't require auto-link.
            raise PackageResolutionError('Boost on Windows requires auto-link')

        # On Windows, check the default install location, which is structured
        # differently from other install locations.
        if not incdir and env.host_platform.family == 'windows':
            dirs = find(r'C:\Boost\include', 'boost-*', type='d', flat=True)
            if dirs:
                try:
                    header = pkg.header(version_hpp, [max(dirs)])
                    libdir = r'C:\Boost\lib'
                except PackageResolutionError:
                    pass

        if header is None:
            header = pkg.header(version_hpp, [incdir] if incdir else None)

        compile_options = opts.option_list(opts.include_dir(header))
        link_options = opts.option_list()
        if libdir:
            link_options.append(opts.lib_dir(Directory(Path(libdir))))
    else:
        header = pkg.header(version_hpp, [incdir] if incdir else None)

        dirs = [libdir] if libdir else None
        libs = (pkg.library('boost_' + i, search_dirs=dirs)
                for i in iterate(name))

        compile_options = opts.option_list()
        link_options = opts.option_list()
        if env.target_platform.family == 'posix' and 'thread' in iterate(name):
            compile_options.append(opts.pthread())
            link_options.append(opts.pthread())

        compile_options.append(opts.include_dir(header))
        link_options.extend(opts.lib(i) for i in libs)

    return BoostPackage(
        name, env.builder('c++').object_format,
        _boost_version(header, version),
        compile_options, link_options
    )
