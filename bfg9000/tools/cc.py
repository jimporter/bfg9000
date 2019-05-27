import os
import re
from itertools import chain
from six import string_types

from . import pkg_config
from .. import log, options as opts, safe_str, shell
from .ar import ArLinker
from .common import (BuildCommand, check_which, darwin_install_name,
                     library_macro)
from .ld import LdLinker
from ..builtins.symlink import Symlink
from ..exceptions import PackageResolutionError
from ..file_types import *
from ..iterutils import (default_sentinel, first, iterate, listify, uniques,
                         recursive_walk)
from ..languages import known_formats
from ..packages import CommonPackage, Framework, PackageKind
from ..path import BasePath, InstallRoot, Path, Root
from ..platforms import parse_triplet
from ..versioning import detect_version, SpecifierSet

_optimize_flags = {
    opts.OptimizeValue.disable : '-O0',
    opts.OptimizeValue.size    : '-Osize',
    opts.OptimizeValue.speed   : '-O3',
    opts.OptimizeValue.linktime: '-flto',
}


class CcBuilder(object):
    def __init__(self, env, langinfo, command, version_output):
        name = langinfo.var('compiler').lower()
        ldinfo = known_formats['native', 'dynamic']
        arinfo = known_formats['native', 'static']

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

        self.lang = langinfo.name
        self.object_format = env.target_platform.object_format

        target_flags = []
        if 'Free Software Foundation' in version_output:
            self.brand = 'gcc'
            self.version = detect_version(version_output)
            if env.is_cross:
                triplet = parse_triplet(env.execute(
                    command + ['-dumpmachine'],
                    stdout=shell.Mode.pipe, stderr=shell.Mode.devnull
                ).rstrip())
                target_flags = self._gcc_arch_flags(
                    env.target_platform.arch, triplet.arch
                )
        elif 'clang' in version_output:
            self.brand = 'clang'
            self.version = detect_version(version_output)
            if env.is_cross:
                target_flags = ['-target', env.target_platform.triplet]
        else:
            self.brand = 'unknown'
            self.version = None

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
        ar_command = check_which(env.getvar(arinfo.var('linker'), 'ar'),
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

        self.compiler = CcCompiler(self, env, name, command, cflags_name,
                                   cflags)
        try:
            self.pch_compiler = CcPchCompiler(self, env, name, command,
                                              cflags_name, cflags)
        except ValueError:
            self.pch_compiler = None

        self._linkers = {
            'executable': CcExecutableLinker(
                self, env, name, link_command, ldflags_name, ldflags,
                ldlibs_name, ldlibs
            ),
            'shared_library': CcSharedLibraryLinker(
                self, env, name, link_command, ldflags_name, ldflags,
                ldlibs_name, ldlibs
            ),
            'static_library': ArLinker(self, env, ar_name, ar_command,
                                       arflags_name, arflags),
        }
        if ld_command:
            self._linkers['raw'] = LdLinker(self, env, ld_command, stdout)

        self.packages = CcPackageResolver(self, env, command, ldflags)
        self.runner = None

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


class CcBaseCompiler(BuildCommand):
    def __init__(self, builder, env, rule_name, command_var, command,
                 cflags_name, cflags):
        BuildCommand.__init__(self, builder, env, rule_name, command_var,
                              command, flags=(cflags_name, cflags))

    @property
    def brand(self):
        return self.builder.brand

    @property
    def version(self):
        return self.builder.version

    @property
    def flavor(self):
        return 'cc'

    @property
    def deps_flavor(self):
        return None if self.lang in ('f77', 'f95') else 'gcc'

    @property
    def num_outputs(self):
        return 1

    @property
    def needs_libs(self):
        return False

    def search_dirs(self, strict=False):
        return [os.path.abspath(i) for i in
                self.env.getvar('CPATH', '').split(os.pathsep)]

    def _call(self, cmd, input, output, deps=None, flags=None):
        result = list(chain(
            cmd, self._always_flags, iterate(flags), ['-c', input]
        ))
        if deps:
            result.extend(['-MMD', '-MF', deps])
        result.extend(['-o', output])
        return result

    @property
    def _always_flags(self):
        flags = ['-x', self._langs[self.lang]]
        # Force color diagnostics on Ninja, since it's off by default. See
        # <https://github.com/ninja-build/ninja/issues/174> for more
        # information.
        if self.env.backend == 'ninja':
            if self.brand == 'clang':
                flags.append('-fcolor-diagnostics')
            elif (self.brand == 'gcc' and self.version and
                  self.version in SpecifierSet('>=4.9')):
                flags.append('-fdiagnostics-color')
        return flags

    def _include_dir(self, directory):
        is_default = ( directory.path.string(self.env.base_dirs) in
                       self.env.host_platform.include_dirs )

        # Don't include default directories as system dirs (e.g. /usr/include).
        # Doing so would break GCC 6 when #including stdlib.h:
        # <https://gcc.gnu.org/bugzilla/show_bug.cgi?id=70129>.
        if directory.system and not is_default:
            return ['-isystem', directory.path]
        else:
            return ['-I' + directory.path]

    def flags(self, options, output=None, mode='normal'):
        flags = []
        for i in options:
            if isinstance(i, opts.include_dir):
                flags.extend(self._include_dir(i.directory))
            elif isinstance(i, opts.define):
                if i.value:
                    flags.append('-D' + i.name + '=' + i.value)
                else:
                    flags.append('-D' + i.name)
            elif isinstance(i, opts.std):
                flags.append('-std=' + i.value)
            elif isinstance(i, opts.warning):
                for j in i.value:
                    if j == opts.WarningValue.disable:
                        flags.append('-w')
                    else:
                        flags.append('-W' + j.name)
            elif isinstance(i, opts.debug):
                flags.append('-g')
            elif isinstance(i, opts.optimize):
                for j in i.value:
                    flags.append(_optimize_flags[j])
            elif isinstance(i, opts.pthread):
                flags.append('-pthread')
            elif isinstance(i, opts.pic):
                flags.append('-fPIC')
            elif isinstance(i, opts.pch):
                flags.extend(['-include', i.header.path.stripext()])
            elif isinstance(i, opts.sanitize):
                flags.append('-fsanitize=address')
            elif isinstance(i, safe_str.stringy_types):
                flags.append(i)
            else:
                raise TypeError('unknown option type {!r}'.format(type(i)))
        return flags


class CcCompiler(CcBaseCompiler):
    _langs = {
        'c'     : 'c',
        'c++'   : 'c++',
        'objc'  : 'objective-c',
        'objc++': 'objective-c++',
        'f77'   : 'f77',
        'f95'   : 'f95',
        'java'  : 'java',
    }

    def __init__(self, builder, env, name, command, cflags_name, cflags):
        CcBaseCompiler.__init__(self, builder, env, name, name, command,
                                cflags_name, cflags)

    @property
    def accepts_pch(self):
        return True

    def output_file(self, name, context):
        # XXX: MinGW's object format doesn't appear to be COFF...
        return ObjectFile(Path(name + '.o'), self.builder.object_format,
                          self.lang)


class CcPchCompiler(CcCompiler):
    _langs = {
        'c'     : 'c-header',
        'c++'   : 'c++-header',
        'objc'  : 'objective-c-header',
        'objc++': 'objective-c++-header',
    }

    def __init__(self, builder, env, name, command, cflags_name, cflags):
        if builder.lang not in self._langs:
            raise ValueError('{} has no precompiled headers'
                             .format(builder.lang))
        CcBaseCompiler.__init__(self, builder, env, name + '_pch', name,
                                command, cflags_name, cflags)

    @property
    def accepts_pch(self):
        # You can't pass a PCH to a PCH compiler!
        return False

    def output_file(self, name, context):
        ext = '.gch' if self.builder.brand == 'gcc' else '.pch'
        return PrecompiledHeader(Path(name + ext), self.lang)


class CcLinker(BuildCommand):
    __allowed_langs = {
        'c'     : {'c'},
        'c++'   : {'c', 'c++', 'f77', 'f95'},
        'objc'  : {'c', 'objc', 'f77', 'f95'},
        'objc++': {'c', 'c++', 'objc', 'objc++', 'f77', 'f95'},
        'f77'   : {'c', 'f77', 'f95'},
        'f95'   : {'c', 'f77', 'f95'},
        'java'  : {'java', 'c', 'c++', 'objc', 'objc++', 'f77', 'f95'},
    }

    def __init__(self, builder, env, rule_name, command_var, command,
                 ldflags_name, ldflags, ldlibs_name, ldlibs):
        BuildCommand.__init__(
            self, builder, env, rule_name, command_var, command,
            flags=(ldflags_name, ldflags), libs=(ldlibs_name, ldlibs)
        )

        # Create a regular expression to extract the library name for linking
        # with -l.
        lib_formats = [r'lib(.*)\.a']
        if not self.env.target_platform.has_import_library:
            so_ext = re.escape(self.env.target_platform.shared_library_ext)
            lib_formats.append(r'lib(.*)' + so_ext)
        self._lib_re = re.compile('(?:' + '|'.join(lib_formats) + ')$')

    def _extract_lib_name(self, library):
        basename = library.path.basename()
        m = self._lib_re.match(basename)
        if not m:
            raise ValueError("'{}' is not a valid library name"
                             .format(basename))

        # Get the first non-None group from the match.
        return next(i for i in m.groups() if i is not None)

    @property
    def brand(self):
        return self.builder.brand

    @property
    def version(self):
        return self.builder.version

    @property
    def flavor(self):
        return 'cc'

    def can_link(self, format, langs):
        return (format == self.builder.object_format and
                self.__allowed_langs[self.lang].issuperset(langs))

    @property
    def needs_libs(self):
        return True

    @property
    def has_link_macros(self):
        # We only need to define LIBFOO_EXPORTS/LIBFOO_STATIC macros on
        # platforms that have different import/export rules for libraries. We
        # approximate this by checking if the platform uses import libraries,
        # and only define the macros if it does.
        return self.env.target_platform.has_import_library

    def sysroot(self, strict=False):
        try:
            # XXX: clang doesn't support -print-sysroot.
            return self.env.execute(
                self.command + self.global_flags + ['-print-sysroot'],
                stdout=shell.Mode.pipe, stderr=shell.Mode.devnull
            ).rstrip()
        except (OSError, shell.CalledProcessError):
            if strict:
                raise
            return '' if self.env.target_platform.family == 'windows' else '/'

    def search_dirs(self, strict=False):
        try:
            output = self.env.execute(
                self.command + self.global_flags + ['-print-search-dirs'],
                stdout=shell.Mode.pipe, stderr=shell.Mode.devnull
            )
            m = re.search(r'^libraries: =(.*)', output, re.MULTILINE)
            search_dirs = re.split(os.pathsep, m.group(1))

            # clang doesn't respect LIBRARY_PATH with -print-search-dirs;
            # see <https://bugs.llvm.org//show_bug.cgi?id=23877>.
            if self.builder.brand == 'clang':
                search_dirs = (self.env.getvar('LIBRARY_PATH', '')
                               .split(os.pathsep)) + search_dirs
        except (OSError, shell.CalledProcessError):
            if strict:
                raise
            search_dirs = self.env.getvar('LIBRARY_PATH', '').split(os.pathsep)
        return [os.path.abspath(i) for i in search_dirs]

    @property
    def num_outputs(self):
        return 1

    def _call(self, cmd, input, output, libs=None, flags=None):
        return list(chain(
            cmd, self._always_flags, iterate(flags), iterate(input),
            iterate(libs), ['-o', output]
        ))

    def pre_build(self, build, name, context):
        entry_point = getattr(context, 'entry_point', None)
        return opts.option_list(opts.entry_point(entry_point) if entry_point
                                else None)

    @property
    def _always_flags(self):
        if self.builder.object_format == 'mach-o':
            return ['-Wl,-headerpad_max_install_names']
        return []

    def _local_rpath(self, library, output):
        if not isinstance(library, Library):
            return [], []

        runtime_lib = library.runtime_file
        if runtime_lib and self.builder.object_format == 'elf':
            path = runtime_lib.path.parent().cross(self.env)
            if path.root != Root.absolute and path.root not in InstallRoot:
                if not output:
                    raise ValueError('unable to construct rpath')
                path = path.relpath(output.path.parent(), prefix='$ORIGIN')
            rpath = [path]

            # Prior to binutils 2.28, GNU's BFD-based ld doesn't correctly
            # respect $ORIGIN in a shared library's DT_RPATH/DT_RUNPATH field.
            # This results in ld being unable to find other shared libraries
            # needed by the directly-linked library. For more information, see:
            # <https://sourceware.org/bugzilla/show_bug.cgi?id=20535>.
            try:
                ld = self.builder.linker('raw')
                fix_rpath = (ld.brand == 'bfd' and ld.version in
                             SpecifierSet('<2.28'))
            except KeyError:
                fix_rpath = False

            rpath_link = []
            if output and fix_rpath:
                rpath_link = [i.path.parent() for i in
                              recursive_walk(runtime_lib, 'runtime_deps')]

            return rpath, rpath_link

        # Either we don't need rpaths or the object format must not support
        # them, so just return nothing.
        return [], []

    def _installed_rpaths(self, options, output):
        result = []
        changed = False
        for i in options:
            if isinstance(i, opts.lib):
                lib = i.library
                if isinstance(lib, Library) and lib.runtime_file:
                    local = self._local_rpath(lib, output)[0][0]
                    installed = file_install_path(lib, cross=self.env).parent()
                    result.append(installed)
                    if not isinstance(local, BasePath) or local != installed:
                        changed = True
            elif isinstance(i, opts.rpath_dir):
                result.append(i.path)

        return uniques(result) if changed else []

    def _darwin_rpath(self, options, output):
        if output and self.builder.object_format == 'mach-o':
            # Currently, we set the rpath on macOS to make it easy to load
            # locally-built shared libraries. Once we install the build, we'll
            # convert all the rpath-based paths to absolute paths and remove
            # the rpath from the binary.
            for i in options:
                if ( isinstance(i, opts.lib) and
                     isinstance(i.library, Library) and not
                     isinstance(i.library, StaticLibrary) ):
                    return Path('.').cross(self.env).relpath(
                        output.path.parent(), prefix='@loader_path'
                    )

        # We didn't find a shared library, or we're just not be building for
        # macOS, so return nothing.
        return None

    def always_libs(self, primary):
        # XXX: Don't just asssume that these are the right libraries to use.
        # For instance, clang users might want to use libc++ instead.
        libs = opts.option_list()
        if self.lang in ('c++', 'objc++') and not primary:
            libs.append(opts.lib('stdc++'))
        if self.lang in ('objc', 'objc++'):
            libs.append(opts.lib('objc'))
        if self.lang in ('f77', 'f95') and not primary:
            libs.append(opts.lib('gfortran'))
        if self.lang == 'java' and not primary:
            libs.append(opts.lib('gcj'))
        return libs

    def _link_lib(self, library, raw_link):
        def common_link(library):
            return ['-l' + self._extract_lib_name(library)]

        if isinstance(library, WholeArchive):
            if self.env.target_platform.genus == 'darwin':
                return ['-Wl,-force_load', library.path]
            return ['-Wl,--whole-archive', library.path,
                    '-Wl,--no-whole-archive']
        elif isinstance(library, Framework):
            if not self.env.target_platform.has_frameworks:
                raise TypeError('frameworks not supported on this platform')
            return ['-framework', library.full_name]
        elif isinstance(library, string_types):
            return ['-l' + library]
        elif isinstance(library, SharedLibrary):
            # If we created this library, we know its soname is set, so passing
            # the raw path to the library works (without soname, the linker
            # would create a reference to the absolute path of the library,
            # which we don't want). We do this to avoid adding more `-L`
            # options than we really need, which makes it easier to find the
            # right library when there are name collisions (e.g. linking to a
            # system `libfoo` when also building a local `libfoo` to use
            # elsewhere).
            if raw_link and library.creator:
                return [library.path]
            return common_link(library)
        elif isinstance(library, StaticLibrary):
            # In addition to the reasons above for shared libraries, we pass
            # static libraries in raw form as a way of avoiding getting the
            # shared version when we don't want it. (There are linker options
            # that do this too, but this way is more compatible and fits with
            # what we already do.)
            if raw_link:
                return [library.path]
            return common_link(library)

        # If we get here, we should have a generic `Library` object (probably
        # from MinGW). The naming for these doesn't work with `-l`, but we'll
        # try just in case and back to emitting the path in raw form.
        try:
            return common_link(library)
        except ValueError:
            if raw_link:
                return [library.path]
            raise

    def _lib_dir(self, library, raw_link):
        if not isinstance(library, Library):
            return []
        elif isinstance(library, StaticLibrary):
            return [] if raw_link else [library.path.parent()]
        elif isinstance(library, SharedLibrary):
            return ([] if raw_link and library.creator else
                    [library.path.parent()])

        # As above, if we get here, we should have a generic `Library` object
        # (probably from MinGW). Use `-L` if the library name works with `-l`;
        # otherwise, return nothing, since the library itself will be passed
        # "raw" (like static libraries).
        try:
            self._extract_lib_name(library)
            return [library.path.parent()]
        except ValueError:
            if raw_link:
                return []
            raise

    def flags(self, options, output=None, mode='normal'):
        raw_link = mode != 'pkg-config'
        flags, rpaths, rpath_links, lib_dirs = [], [], [], []
        rpaths.extend(iterate(self._darwin_rpath(options, output)))

        for i in options:
            if isinstance(i, opts.lib_dir):
                lib_dirs.append(i.directory.path)
            elif isinstance(i, opts.lib):
                lib_dirs.extend(self._lib_dir(i.library, raw_link))
                rp, rplink = self._local_rpath(i.library, output)
                rpaths.extend(rp)
                rpath_links.extend(rplink)
            elif isinstance(i, opts.rpath_dir):
                rpaths.append(i.path)
            elif isinstance(i, opts.rpath_link_dir):
                rpath_links.append(i.path)
            elif isinstance(i, opts.module_def):
                if self.env.target_platform.has_import_library:
                    flags.append(i.value.path)
            elif isinstance(i, opts.debug):
                flags.append('-g')
            elif isinstance(i, opts.optimize):
                for j in i.value:
                    flags.append(_optimize_flags[j])
            elif isinstance(i, opts.pthread):
                # macOS doesn't expect -pthread when linking.
                if self.env.target_platform.genus != 'darwin':
                    flags.append('-pthread')
            elif isinstance(i, opts.entry_point):
                if self.lang != 'java':
                    raise ValueError('entry point only applies to java')
                flags.append('--main={}'.format(i.value))
            elif isinstance(i, safe_str.stringy_types):
                flags.append(i)
            elif isinstance(i, opts.lib_literal):
                pass
            else:
                raise TypeError('unknown option type {!r}'.format(type(i)))

        flags.extend('-L' + i for i in uniques(lib_dirs))
        if rpaths:
            flags.append('-Wl,-rpath,' + safe_str.join(rpaths, ':'))
        if rpath_links:
            flags.append('-Wl,-rpath-link,' + safe_str.join(rpath_links, ':'))
        return flags

    def lib_flags(self, options, mode='normal'):
        raw_link = mode != 'pkg-config'
        flags = []
        for i in options:
            if isinstance(i, opts.lib):
                flags.extend(self._link_lib(i.library, raw_link))
            elif isinstance(i, opts.lib_literal):
                flags.append(i.value)
        return flags

    def post_install(self, options, output, context):
        if self.builder.object_format not in ['elf', 'mach-o']:
            return None

        path = file_install_path(output)

        if self.builder.object_format == 'elf':
            rpath = self._installed_rpaths(options, output)
            return self.env.tool('patchelf')(path, rpath)
        else:  # mach-o
            rpath = self._darwin_rpath(options, output)
            changes = [(darwin_install_name(i),
                        file_install_path(i, cross=self.env))
                       for i in output.runtime_deps]
            return self.env.tool('install_name_tool')(
                path, path if self._is_library else None, rpath, changes
            )


class CcExecutableLinker(CcLinker):
    _is_library = False

    def __init__(self, builder, env, name, command, ldflags_name, ldflags,
                 ldlibs_name, ldlibs):
        CcLinker.__init__(self, builder, env, name + '_link', name, command,
                          ldflags_name, ldflags, ldlibs_name, ldlibs)

    def output_file(self, name, context):
        path = Path(name + self.env.target_platform.executable_ext)
        return Executable(path, self.builder.object_format, self.lang)


class CcSharedLibraryLinker(CcLinker):
    _is_library = True

    def __init__(self, builder, env, name, command, ldflags_name, ldflags,
                 ldlibs_name, ldlibs):
        CcLinker.__init__(self, builder, env, name + '_linklib', name, command,
                          ldflags_name, ldflags, ldlibs_name, ldlibs)

    @property
    def num_outputs(self):
        return 2 if self.env.target_platform.has_import_library else 1

    def _call(self, cmd, input, output, libs=None, flags=None):
        output = listify(output)
        result = CcLinker._call(self, cmd, input, output[0], libs, flags)
        if self.env.target_platform.has_import_library:
            result.append('-Wl,--out-implib=' + output[1])
        return result

    def _lib_name(self, name, prefix='lib', suffix=''):
        head, tail = Path(name).splitleaf()
        ext = self.env.target_platform.shared_library_ext
        return head.append(prefix + tail + ext + suffix)

    def post_build(self, build, options, output, context):
        if isinstance(output, VersionedSharedLibrary):
            # Make symlinks for the various versions of the shared lib.
            Symlink(build, output.soname, output)
            Symlink(build, output.link, output.soname)
            return output.link

    def output_file(self, name, context):
        version = getattr(context, 'version', None)
        soversion = getattr(context, 'soversion', None)
        fmt = self.builder.object_format

        if version and self.env.target_platform.has_versioned_library:
            if self.env.target_platform.genus == 'darwin':
                real = self._lib_name(name + '.{}'.format(version))
                soname = self._lib_name(name + '.{}'.format(soversion))
            else:
                real = self._lib_name(name, suffix='.{}'.format(version))
                soname = self._lib_name(name, suffix='.{}'.format(soversion))
            link = self._lib_name(name)
            return VersionedSharedLibrary(real, fmt, self.lang, soname, link)
        elif self.env.target_platform.has_import_library:
            dllprefix = ('cyg' if self.env.target_platform.genus == 'cygwin'
                         else '')
            dllname = self._lib_name(name, prefix=dllprefix)
            impname = self._lib_name(name, suffix='.a')
            dll = DllBinary(dllname, fmt, self.lang, impname)
            return [dll, dll.import_lib]
        else:
            return SharedLibrary(self._lib_name(name), fmt, self.lang)

    @property
    def _always_flags(self):
        shared = ('-dynamiclib' if self.env.target_platform.genus == 'darwin'
                  else '-shared')
        return CcLinker._always_flags.fget(self) + [shared, '-fPIC']

    def _soname(self, library):
        if isinstance(library, VersionedSharedLibrary):
            soname = library.soname
        else:
            soname = library

        if self.env.target_platform.genus == 'darwin':
            return ['-install_name', darwin_install_name(soname)]
        else:
            return ['-Wl,-soname,' + soname.path.basename()]

    def compile_options(self, context):
        options = opts.option_list()
        if self.builder.object_format != 'coff':
            options.append(opts.pic())
        if self.has_link_macros:
            options.append(opts.define(library_macro(
                context.name, 'shared_library'
            )))
        return options

    def flags(self, options, output=None, mode='normal'):
        flags = CcLinker.flags(self, options, output, mode)
        if output:
            flags.extend(self._soname(first(output)))
        return flags


class CcPackageResolver(object):
    def __init__(self, builder, env, command, ldflags):
        self.builder = builder
        self.env = env

        self.include_dirs = [i for i in uniques(chain(
            self.builder.compiler.search_dirs(),
            self.env.host_platform.include_dirs
        )) if os.path.exists(i)]

        cc_lib_dirs = self.builder.linker('executable').search_dirs()
        try:
            sysroot = self.builder.linker('executable').sysroot()
            ld_lib_dirs = self.builder.linker('raw').search_dirs(sysroot, True)
        except (KeyError, OSError, shell.CalledProcessError):
            ld_lib_dirs = self.env.host_platform.lib_dirs

        self.lib_dirs = [i for i in uniques(chain(
            cc_lib_dirs, ld_lib_dirs, self.env.host_platform.lib_dirs
        )) if os.path.exists(i)]

    @property
    def lang(self):
        return self.builder.lang

    def header(self, name, search_dirs=None):
        if search_dirs is None:
            search_dirs = self.include_dirs

        for base in search_dirs:
            if os.path.exists(os.path.join(base, name)):
                return HeaderDirectory(Path(base, Root.absolute), None,
                                       system=True, external=True)

        raise PackageResolutionError("unable to find header '{}'".format(name))

    def library(self, name, kind=PackageKind.any, search_dirs=None):
        if search_dirs is None:
            search_dirs = self.lib_dirs

        libnames = []
        if kind & PackageKind.shared:
            base = 'lib' + name + self.env.target_platform.shared_library_ext
            if self.env.target_platform.has_import_library:
                libnames.append((base + '.a', LinkLibrary, {}))
            else:
                libnames.append((base, SharedLibrary, {}))
        if kind & PackageKind.static:
            libnames.append(('lib' + name + '.a', StaticLibrary,
                             {'lang': self.lang}))

        # XXX: Include Cygwin here too?
        if self.env.target_platform.family == 'windows':
            # We don't actually know what kind of library this is. It could be
            # a static library or an import library (which we classify as a
            # kind of shared lib).
            libnames.append((name + '.lib', Library, {}))

        for base in search_dirs:
            for libname, libkind, extra_kwargs in libnames:
                fullpath = os.path.join(base, libname)
                if os.path.exists(fullpath):
                    return libkind(Path(fullpath, Root.absolute),
                                   format=self.builder.object_format,
                                   external=True, **extra_kwargs)

        raise PackageResolutionError("unable to find library '{}'"
                                     .format(name))

    def resolve(self, name, version, kind, headers, lib_names):
        format = self.builder.object_format
        try:
            return pkg_config.resolve(self.env, name, format, version, kind)
        except (OSError, PackageResolutionError):
            compile_options = opts.option_list()
            link_options = opts.option_list()

            compile_options.extend(opts.include_dir(self.header(i))
                                   for i in iterate(headers))

            if lib_names is default_sentinel:
                lib_names = self.env.target_platform.transform_package(name)
            for i in iterate(lib_names):
                if isinstance(i, Framework):
                    link_options.append(opts.lib(i))
                elif i == 'pthread':
                    compile_options.append(opts.pthread())
                    link_options.append(opts.pthread())
                else:
                    link_options.append(opts.lib(self.library(i, kind)))

            return CommonPackage(name, format, compile_options, link_options)
