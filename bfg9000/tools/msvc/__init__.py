import os.path
from itertools import chain

from .. import mopack, pkg_config
from ... import shell
from .compiler import MsvcCompiler, MsvcPchCompiler
from .linker import (MsvcExecutableLinker, MsvcSharedLibraryLinker,
                     MsvcStaticLinker)
from .rc import MsvcRcBuilder  # noqa: F401
from ..common import Builder, check_which
from ...iterutils import uniques
from ...languages import known_formats
from ...path import exists
from ...versioning import detect_version


class MsvcBuilder(Builder):
    def __init__(self, env, langinfo, command, found, version_output):
        brand, version = self._parse_brand(env, command, version_output)
        super().__init__(langinfo.name, brand, version)
        self.object_format = env.target_platform.object_format

        name = langinfo.var('compiler').lower()
        ldinfo = known_formats['native']['dynamic']
        arinfo = known_formats['native']['static']

        # Look for the last argument that looks like our compiler and use its
        # directory as the base directory to find the linkers.
        origin = ''
        for i in reversed(command):
            if os.path.basename(i) in ('cl', 'cl.exe'):
                origin = os.path.dirname(i)
        link_which = check_which(
            env.getvar(ldinfo.var('linker'), os.path.join(origin, 'link')),
            env.variables, kind='{} dynamic linker'.format(self.lang)
        )
        lib_which = check_which(
            env.getvar(arinfo.var('linker'), os.path.join(origin, 'lib')),
            env.variables, kind='{} static linker'.format(self.lang)
        )

        cflags_name = langinfo.var('flags').lower()
        cflags = (
            shell.split(env.getvar('CPPFLAGS', '')) +
            shell.split(env.getvar(langinfo.var('flags'), ''))
        )

        ld_name = ldinfo.var('linker').lower()
        ldflags_name = ldinfo.var('flags').lower()
        ldflags = shell.split(env.getvar(ldinfo.var('flags'), ''))
        ldlibs_name = ldinfo.var('libs').lower()
        ldlibs = shell.split(env.getvar(ldinfo.var('libs'), ''))

        ar_name = arinfo.var('linker').lower()
        arflags_name = arinfo.var('flags').lower()
        arflags = shell.split(env.getvar(arinfo.var('flags'), ''))

        compile_kwargs = {'command': (name, command, found),
                          'flags': (cflags_name, cflags)}
        self.compiler = MsvcCompiler(self, env, **compile_kwargs)
        self.pch_compiler = MsvcPchCompiler(self, env, **compile_kwargs)

        link_kwargs = {'command': (ld_name,) + link_which,
                       'flags': (ldflags_name, ldflags),
                       'libs': (ldlibs_name, ldlibs)}
        self._linkers = {
            'executable': MsvcExecutableLinker(self, env, name, **link_kwargs),
            'shared_library': MsvcSharedLibraryLinker(self, env, name,
                                                      **link_kwargs),
            'static_library': MsvcStaticLinker(
                self, env, command=(ar_name,) + lib_which,
                flags=(arflags_name, arflags)
            ),
        }
        self.packages = MsvcPackageResolver(self, env)
        self.runner = None

    @staticmethod
    def _parse_brand(env, command, version_output):
        if 'Microsoft (R)' in version_output:
            return 'msvc', detect_version(version_output)
        elif 'clang LLVM compiler' in version_output:
            real_version = env.execute(
                command + ['--version'], stdout=shell.Mode.pipe,
                stderr=shell.Mode.stdout
            )
            return 'clang', detect_version(real_version)

        return 'unknown', None

    @staticmethod
    def check_command(env, command):
        return env.execute(command + ['-?'], stdout=shell.Mode.pipe,
                           stderr=shell.Mode.stdout)

    @property
    def flavor(self):
        return 'msvc'

    @property
    def family(self):
        return 'native'

    @property
    def auto_link(self):
        return True

    @property
    def can_dual_link(self):
        return False

    def linker(self, mode):
        return self._linkers[mode]


class MsvcPackageResolver:
    _lib_names = ['{}.lib']

    def __init__(self, builder, env):
        self.builder = builder
        self.env = env

        self.include_dirs = [i for i in uniques(chain(
            self.builder.compiler.search_dirs(),
            self.env.host_platform.include_dirs
        )) if exists(i)]

        self.lib_dirs = [i for i in uniques(chain(
            self.builder.linker('executable').search_dirs(),
            self.env.host_platform.lib_dirs
        )) if exists(i)]

    @property
    def lang(self):
        return self.builder.lang

    # TODO: Remove headers/libs from arguments after 0.7 is released.
    def resolve(self, name, submodules, version, kind, *, headers=None,
                libs=None, system=True):
        format = self.builder.object_format
        usage = mopack.get_usage(self.env, name, submodules, self.include_dirs,
                                 self.lib_dirs, self._lib_names)

        # XXX: Add headers/libs here somehow? Add them into PkgConfigPackage
        # directly?
        return pkg_config.resolve(
            self.env, name, submodules, version, usage['pcnames'],
            format=format, kind=kind, system=system,
            search_path=usage['pkg_config_path'],
            generated=usage.get('generated', False)
        )
