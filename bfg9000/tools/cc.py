import os.path
import re
import subprocess
from itertools import chain

from . import pkg_config
from .. import safe_str
from .. import shell
from .ar import ArLinker
from .common import BuildCommand, darwin_install_name
from .ld import LdLinker
from ..builtins.symlink import Symlink
from ..exceptions import PackageResolutionError
from ..file_types import *
from ..iterutils import (default_sentinel, first, iterate, listify, uniques,
                         recursive_walk)
from ..path import install_path, Path, Root
from ..versioning import detect_version, SpecifierSet


class CcBuilder(object):
    def __init__(self, env, lang, name, command, cflags_name, cflags,
                 version_output):
        self.lang = lang
        self.object_format = env.platform.object_format

        if 'Free Software Foundation' in version_output:
            self.brand = 'gcc'
            self.version = detect_version(version_output)
        elif 'clang' in version_output:
            self.brand = 'clang'
            self.version = detect_version(version_output)
        else:
            self.brand = 'unknown'
            self.version = None

        ldflags = shell.split(env.getvar('LDFLAGS', ''))
        ldlibs = shell.split(env.getvar('LDLIBS', ''))

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
                self, env, name, command, ldflags, ldlibs
            ),
            'shared_library': CcSharedLibraryLinker(
                self, env, name, command, ldflags, ldlibs
            ),
            'static_library': ArLinker(self, env),
        }
        if ld_command:
            self._linkers['raw'] = LdLinker(self, env, ld_command, stdout)

        self.packages = CcPackageResolver(self, env, command, ldflags)
        self.runner = None

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
    def depends_on_libs(self):
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
            if self.builder.brand == 'clang':
                flags += ['-fcolor-diagnostics']
            elif (self.builder.brand == 'gcc' and self.builder.version and
                  self.builder.version in SpecifierSet('>=4.9')):
                flags += ['-fdiagnostics-color']
        return flags

    def _include_dir(self, directory):
        is_default = ( directory.path.string(self.env.base_dirs) in
                       self.env.platform.include_dirs )

        # Don't include default directories as system dirs (e.g. /usr/include).
        # Doing so would break GCC 6 when #including stdlib.h:
        # <https://gcc.gnu.org/bugzilla/show_bug.cgi?id=70129>.
        if directory.system and not is_default:
            return ['-isystem', directory.path]
        else:
            return ['-I' + directory.path]

    def _include_pch(self, pch):
        return ['-include', pch.path.stripext()]

    def _pthread(self, pthread):
        return ['-pthread'] if pthread else []

    def flags(self, options, output, pkg=False):
        pthread = getattr(options, 'pthread', False)
        includes = getattr(options, 'includes', [])
        pch = getattr(options, 'pch', None)

        return (self._pthread(pthread) +
                sum((self._include_dir(i) for i in includes), []) +
                (self._include_pch(pch) if pch else []))

    def link_flags(self, mode, defines):
        flags = []
        if ( mode in ['shared_library', 'static_library'] and
             self.env.platform.flavor != 'windows'):
            flags.append('-fPIC')

        flags.extend('-D' + i for i in defines)
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

    def output_file(self, name, options):
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
        if builder.lang == 'java':
            raise ValueError('Java has no precompiled headers')
        CcBaseCompiler.__init__(self, builder, env, name + '_pch', name,
                                command, cflags_name, cflags)

    @property
    def accepts_pch(self):
        # You can't pass a PCH to a PCH compiler!
        return False

    def output_file(self, name, options):
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

    def __init__(self, builder, env, rule_name, command_var, command, ldflags,
                 ldlibs):
        BuildCommand.__init__(
            self, builder, env, rule_name, command_var, command,
            flags=('ldflags', ldflags), libs=('ldlibs', ldlibs)
        )

        # Create a regular expression to extract the library name for linking
        # with -l.
        lib_formats = [r'lib(.*)\.a']
        if not self.env.platform.has_import_library:
            so_ext = re.escape(self.env.platform.shared_library_ext)
            lib_formats.append(r'lib(.*)' + so_ext)
        # XXX: Include Cygwin here too?
        if self.env.platform.name == 'windows':
            lib_formats.append(r'(.*)\.lib')
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
    def has_link_macros(self):
        # We only need to define LIBFOO_EXPORTS/LIBFOO_STATIC macros on
        # platforms that have different import/export rules for libraries. We
        # approximate this by checking if the platform uses import libraries,
        # and only define the macros if it does.
        return self.env.platform.has_import_library

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
            return '' if self.env.platform.flavor == 'windows' else '/'

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

    @property
    def _always_flags(self):
        if self.builder.object_format == 'mach-o':
            return ['-Wl,-headerpad_max_install_names']
        return []

    def _lib_dirs(self, libraries, extra_dirs):
        dirs = uniques(chain(
            (i.path.parent() for i in iterate(libraries)
             if isinstance(i, Library) and not isinstance(i, StaticLibrary)),
            extra_dirs
        ))
        return ['-L' + i for i in dirs]

    def _rpath(self, libraries, extra_dirs, output):
        if not output:
            return []

        runtime_libs = [i.runtime_file for i in libraries if i.runtime_file]
        if not runtime_libs and not extra_dirs:
            return []

        if self.builder.object_format == 'elf':
            start = output.path.parent()
            base = '$ORIGIN'
            paths = uniques(chain((i.path.parent() for i in runtime_libs),
                                  extra_dirs))

            relpaths = (i.relpath(start) for i in paths)
            result = ['-Wl,-rpath,{}'.format(':'.join(
                base if i == '.' else os.path.join(base, i) for i in relpaths
            ))]

            # Store the final (installed) rpaths so we can apply them with
            # `patchelf` during installation.
            output._rpath = uniques(chain(
                getattr(output, '_rpath', []),
                (install_path(i.path, i.install_root, destdir=False).parent()
                 for i in runtime_libs),
                extra_dirs
            ))

            # GNU's BFD-based ld doesn't correctly respect $ORIGIN in a shared
            # library's DT_RPATH/DT_RUNPATH field. This results in ld being
            # unable to find other shared libraries needed by the directly-
            # linked library. For more information, see:
            # <https://sourceware.org/bugzilla/show_bug.cgi?id=16936>.
            try:
                brand = self.builder.linker('raw').brand
            except KeyError:
                # Assume the brand is bfd, since setting -rpath-link shouldn't
                # hurt anything.
                brand = 'bfd'

            if brand == 'bfd':
                deps = chain.from_iterable(recursive_walk(i, 'runtime_deps')
                                           for i in runtime_libs)
                dep_paths = [i for i in uniques(i.path.parent() for i in deps)]
                if dep_paths:
                    result += ['-Wl,-rpath-link,' +
                               safe_str.join(dep_paths, ':')]

            return result
        elif self.builder.object_format == 'mach-o':
            # Currently, we set the rpath on macOS to make it easy to load
            # locally-built shared libraries. Once we install the build, we'll
            # convert all the rpath-based paths to absolute paths and remove
            # the rpath from the binary.
            base = '@loader_path'
            path = Path('.').relpath(output.path.parent())
            # Store the temporary rpath so we can remove it during installation
            # with `install_name_tool`.
            output._rpath = (base if path == '.' else os.path.join(base, path))
            return ['-Wl,-rpath,' + output._rpath]
        else:
            # This object format must not support rpaths, so just return.
            return []

    def _pthread(self, pthread):
        # macOS doesn't expect -pthread when linking.
        if pthread and self.env.platform.name != 'darwin':
            return ['-pthread']
        return []

    def _entry_point(self, entry_point):
        if self.lang == 'java' and entry_point:
            return ['--main={}'.format(entry_point)]
        return []

    def flags(self, options, output, pkg=False):
        pthread = getattr(options, 'pthread', False)
        libraries = getattr(options, 'libs', [])
        lib_dirs = getattr(options, 'lib_dirs', [])
        rpath_dirs = getattr(options, 'rpath_dirs', [])
        entry_point = getattr(options, 'entry_point', None)

        return (self._pthread(pthread) +
                self._lib_dirs(libraries, lib_dirs) +
                self._rpath(libraries, rpath_dirs, output) +
                self._entry_point(entry_point))

    def _link_lib(self, library, raw_static):
        if isinstance(library, WholeArchive):
            if self.env.platform.name == 'darwin':
                return ['-Wl,-force_load', library.path]
            return ['-Wl,--whole-archive', library.path,
                    '-Wl,--no-whole-archive']
        elif isinstance(library, Framework):
            if not self.env.platform.has_frameworks:
                raise TypeError('frameworks not supported on this platform')
            return ['-framework', library.full_name]
        elif isinstance(library, StaticLibrary) and raw_static:
            return [library.path]

        # If we're here, we have a SharedLibrary (or possibly just a Library
        # in the case of MinGW).
        return ['-l' + self._extract_lib_name(library)]

    def always_libs(self, primary):
        # XXX: Don't just asssume that these are the right libraries to use.
        # For instance, clang users might want to use libc++ instead.
        libs = []
        if self.lang in ('c++', 'objc++') and not primary:
            libs.append('-lstdc++')
        if self.lang in ('objc', 'objc++'):
            libs.append('-lobjc')
        if self.lang in ('f77', 'f95') and not primary:
            libs.append('-lgfortran')
        if self.lang == 'java' and not primary:
            libs.append('-lgcj')
        return libs

    def libs(self, options, output, pkg=False):
        libraries = getattr(options, 'libs', [])
        raw_static = getattr(options, 'raw_static', True)
        return sum((self._link_lib(i, raw_static) for i in libraries), [])

    def _post_install(self, output, library):
        if self.builder.object_format not in ['elf', 'mach-o']:
            return None

        path = install_path(output.path, output.install_root)
        rpath = getattr(output, '_rpath', None)
        if self.builder.object_format == 'elf':
            return self.env.tool('patchelf')(path, rpath)
        else:  # mach-o
            changes = [(darwin_install_name(i),
                        install_path(i.path, i.install_root, destdir=False))
                       for i in output.runtime_deps]
            return self.env.tool('install_name_tool')(
                path, path if library else None, rpath, changes
            )

    def post_install(self, output):
        return self._post_install(output, False)


class CcExecutableLinker(CcLinker):
    def __init__(self, builder, env, name, command, ldflags, ldlibs):
        CcLinker.__init__(self, builder, env, name + '_link', name, command,
                          ldflags, ldlibs)

    def output_file(self, name, options):
        path = Path(name + self.env.platform.executable_ext)
        return Executable(path, self.builder.object_format, self.lang)


class CcSharedLibraryLinker(CcLinker):
    def __init__(self, builder, env, name, command, ldflags, ldlibs):
        CcLinker.__init__(self, builder, env, name + '_linklib', name, command,
                          ldflags, ldlibs)

    @property
    def num_outputs(self):
        return 2 if self.env.platform.has_import_library else 1

    def _call(self, cmd, input, output, libs=None, flags=None):
        output = listify(output)
        result = CcLinker._call(self, cmd, input, output[0], libs, flags)
        if self.env.platform.has_import_library:
            result.append('-Wl,--out-implib=' + output[1])
        return result

    def post_build(self, build, options, output):
        if isinstance(output, VersionedSharedLibrary):
            # Make symlinks for the various versions of the shared lib.
            Symlink(build, output.soname, output)
            Symlink(build, output.link, output.soname)
            return output.link

    def output_file(self, name, options):
        version = getattr(options, 'version', None)
        soversion = getattr(options, 'soversion', None)

        head, tail = os.path.split(name)
        fmt = self.builder.object_format

        def lib(head, tail, prefix='lib', suffix=''):
            ext = self.env.platform.shared_library_ext
            return Path(os.path.join(
                head, prefix + tail + ext + suffix
            ))

        if self.env.platform.has_import_library:
            dllprefix = 'cyg' if self.env.platform.name == 'cygwin' else 'lib'
            dllname = lib(head, tail, dllprefix)
            impname = lib(head, tail, suffix='.a')
            dll = DllBinary(dllname, fmt, self.lang, impname)
            return [dll, dll.import_lib]
        elif version and self.env.platform.has_versioned_library:
            if self.env.platform.name == 'darwin':
                real = lib(head, '{}.{}'.format(tail, version))
                soname = lib(head, '{}.{}'.format(tail, soversion))
            else:
                real = lib(head, tail, suffix='.{}'.format(version))
                soname = lib(head, tail, suffix='.{}'.format(soversion))
            link = lib(head, tail)
            return VersionedSharedLibrary(real, fmt, self.lang, soname, link)
        else:
            return SharedLibrary(lib(head, tail), fmt, self.lang)

    @property
    def _always_flags(self):
        shared = ('-dynamiclib' if self.env.platform.name == 'darwin'
                  else '-shared')
        return CcLinker._always_flags.fget(self) + [shared, '-fPIC']

    def _soname(self, library):
        if isinstance(library, VersionedSharedLibrary):
            soname = library.soname
        else:
            soname = library

        if self.env.platform.name == 'darwin':
            return ['-install_name', darwin_install_name(soname)]
        else:
            return ['-Wl,-soname,' + soname.path.basename()]

    def flags(self, options, output, pkg=False):
        flags = CcLinker.flags(self, options, output, pkg)
        if not pkg:
            flags.extend(self._soname(first(output)))
        return flags

    def post_install(self, output):
        return self._post_install(output, True)


class CcPackageResolver(object):
    def __init__(self, builder, env, command, ldflags):
        self.builder = builder
        self.env = env

        self.include_dirs = [i for i in uniques(chain(
            self.builder.compiler.search_dirs(), self.env.platform.include_dirs
        )) if os.path.exists(i)]

        cc_lib_dirs = self.builder.linker('executable').search_dirs()
        try:
            sysroot = self.builder.linker('executable').sysroot()
            ld_lib_dirs = self.builder.linker('raw').search_dirs(sysroot, True)
        except (KeyError, OSError, shell.CalledProcessError):
            ld_lib_dirs = self.env.platform.lib_dirs

        self.lib_dirs = [i for i in uniques(chain(
            cc_lib_dirs, ld_lib_dirs, self.env.platform.lib_dirs
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
            libname = 'lib' + name + self.env.platform.shared_library_ext
            if self.env.platform.has_import_library:
                libnames.append((libname + '.a', LinkLibrary, {}))
            else:
                libnames.append((libname, SharedLibrary, {}))
        if kind & PackageKind.static:
            libnames.append(('lib' + name + '.a', StaticLibrary,
                             {'lang': self.lang}))

        # XXX: Include Cygwin here too?
        if self.env.platform.name == 'windows':
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
            if lib_names is default_sentinel:
                lib_names = self.env.platform.transform_package(name)
            includes = [self.header(i) for i in iterate(headers)]

            extra_kwargs = {}
            libs = []
            for i in iterate(lib_names):
                if isinstance(i, Framework):
                    libs.append(i)
                elif i == 'pthread':
                    extra_kwargs['pthread'] = True
                else:
                    libs.append(self.library(i, kind))

            return CommonPackage(name, format, includes=includes, libs=libs,
                                 **extra_kwargs)
