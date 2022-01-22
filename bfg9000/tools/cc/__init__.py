import os
import re
from itertools import chain

from .. import mopack, pkg_config
from ... import log, shell
from .compiler import CcCompiler, CcPchCompiler
from .linker import CcExecutableLinker, CcSharedLibraryLinker
from .rc import CcRcBuilder  # noqa: F401
from ..ar import ArLinker
from ..common import Builder, check_which
from ..ld import LdLinker
from ...exceptions import PackageResolutionError
from ...iterutils import uniques
from ...languages import known_formats
from ...packages import PackageKind
from ...path import exists
from ...platforms import parse_triplet
from ...versioning import detect_version


class CcBuilder(Builder):
    def __init__(self, env, langinfo, command, found, version_output):
        brand, version, target_flags = self._parse_brand(env, command,
                                                         version_output)
        super().__init__(langinfo.name, brand, version)
        self.object_format = env.target_platform.object_format

        name = langinfo.var('compiler').lower()
        ldinfo = known_formats['native']['dynamic']
        arinfo = known_formats['native']['static']

        # Try to infer the appropriate -fuse-ld option from the LD environment
        # variable.
        link_command = command[:]
        ld_command = env.getvar(ldinfo.var('linker'))
        if ld_command:
            tail = os.path.splitext(ld_command)[1][1:]
            if tail in ['bfd', 'gold']:
                log.info('setting `-fuse-ld={}` for `{}`'
                         .format(tail, shell.join(command)))
                link_command.append('-fuse-ld={}'.format(tail))

        cflags_name = langinfo.var('flags').lower()
        cflags = (target_flags +
                  shell.split(env.getvar('CPPFLAGS', '')) +
                  shell.split(env.getvar(langinfo.var('flags'), '')))

        ldflags_name = ldinfo.var('flags').lower()
        ldflags = (target_flags +
                   shell.split(env.getvar(ldinfo.var('flags'), '')))
        ldlibs_name = ldinfo.var('libs').lower()
        ldlibs = shell.split(env.getvar(ldinfo.var('libs'), ''))

        ar_name = arinfo.var('linker').lower()
        ar_which = check_which(env.getvar(arinfo.var('linker'), 'ar'),
                               env.variables, kind='static linker')
        arflags_name = arinfo.var('flags').lower()
        arflags = shell.split(env.getvar(arinfo.var('flags'), 'cr'))

        # macOS's ld doesn't support --version, but we can still try it out and
        # grab the command line.
        ld_command = None
        try:
            stdout, stderr = env.execute(
                command + ldflags + ['-v', '-Wl,--version'],
                stdout=shell.Mode.pipe, stderr=shell.Mode.pipe,
                returncode='any'
            )

            for line in stderr.split('\n'):
                if '--version' in line:
                    ld_command = shell.split(line)[0:1]
                    if os.path.basename(ld_command[0]) != 'collect2':
                        break
        except (OSError, shell.CalledProcessError):
            pass

        compile_kwargs = {'command': (name, command, found),
                          'flags': (cflags_name, cflags)}
        self.compiler = CcCompiler(self, env, **compile_kwargs)
        try:
            self.pch_compiler = CcPchCompiler(self, env, **compile_kwargs)
        except ValueError:
            self.pch_compiler = None

        link_kwargs = {'command': (name, link_command, found),
                       'flags': (ldflags_name, ldflags),
                       'libs': (ldlibs_name, ldlibs)}
        self._linkers = {
            'executable': CcExecutableLinker(self, env, **link_kwargs),
            'shared_library': CcSharedLibraryLinker(self, env, **link_kwargs),
            'static_library': ArLinker(
                self, env, command=(ar_name,) + ar_which,
                flags=(arflags_name, arflags)
            ),
        }
        if ld_command:
            self._linkers['raw'] = LdLinker(self, env, ld_command, stdout)

        self.packages = CcPackageResolver(self, env, command, ldflags)
        self.runner = None

    @classmethod
    def _parse_brand(cls, env, command, version_output):
        target_flags = []
        if 'Free Software Foundation' in version_output:
            brand = 'gcc'
            version = detect_version(version_output)
            if env.is_cross:
                triplet = parse_triplet(env.execute(
                    command + ['-dumpmachine'],
                    stdout=shell.Mode.pipe, stderr=shell.Mode.devnull
                ).rstrip())
                target_flags = cls._gcc_arch_flags(
                    env.target_platform.arch, triplet.arch
                )
        elif 'clang' in version_output:
            brand = 'clang'
            version = detect_version(version_output)
            if env.is_cross:
                target_flags = ['-target', env.target_platform.triplet]
        else:
            brand = 'unknown'
            version = None

        return brand, version, target_flags

    @staticmethod
    def _gcc_arch_flags(arch, native_arch):
        if arch == native_arch:
            return []
        elif arch == 'x86_64':
            return ['-m64']
        elif re.match(r'i.86$', arch):
            return ['-m32'] if not re.match(r'i.86$', native_arch) else []
        return []

    @staticmethod
    def check_command(env, command):
        return env.execute(command + ['--version'], stdout=shell.Mode.pipe,
                           stderr=shell.Mode.devnull)

    @property
    def flavor(self):
        return 'cc'

    @property
    def family(self):
        return 'native'

    @property
    def auto_link(self):
        return False

    @property
    def can_dual_link(self):
        return True

    def linker(self, mode):
        return self._linkers[mode]


class CcPackageResolver:
    def __init__(self, builder, env, command, ldflags):
        self.builder = builder
        self.env = env

        self.include_dirs = [i for i in uniques(chain(
            self.builder.compiler.search_dirs(),
            self.env.host_platform.include_dirs
        )) if exists(i)]

        cc_lib_dirs = self.builder.linker('executable').search_dirs()
        try:
            sysroot = self.builder.linker('executable').sysroot()
            ld_lib_dirs = self.builder.linker('raw').search_dirs(sysroot, True)
        except (KeyError, OSError, shell.CalledProcessError):
            ld_lib_dirs = self.env.host_platform.lib_dirs

        self.lib_dirs = [i for i in uniques(chain(
            cc_lib_dirs, ld_lib_dirs, self.env.host_platform.lib_dirs
        )) if exists(i)]

    @property
    def lang(self):
        return self.builder.lang

    def _lib_names(self, kind):
        names = []
        if kind & PackageKind.shared:
            base = 'lib{}' + self.env.target_platform.shared_library_ext
            if self.env.target_platform.has_import_library:
                names.append(base + '.a')
            else:
                names.append(base)
        if kind & PackageKind.static:
            names.append('lib{}.a')

        # XXX: Include Cygwin here too?
        if self.env.target_platform.family == 'windows':
            names.append('{}.lib')
        return names

    # TODO: Remove headers/libs from arguments after 0.7 is released.
    def resolve(self, name, submodules, version, kind, *, headers=None,
                libs=None, system=True):
        format = self.builder.object_format
        usage = mopack.get_usage(self.env, name, submodules, self.include_dirs,
                                 self.lib_dirs, self._lib_names(kind))
        if usage.get('auto_link', False):
            raise PackageResolutionError('package {!r} requires auto-link'
                                         .format(name))

        # XXX: Add headers/libs here somehow? Add them into PkgConfigPackage
        # directly?
        return pkg_config.resolve(
            self.env, name, submodules, version, usage['pcnames'],
            format=format, kind=kind, system=system,
            search_path=usage['pkg_config_path'],
            generated=usage.get('generated', False)
        )
