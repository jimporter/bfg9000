import os.path
import re
import subprocess
from itertools import chain
from six.moves import filter as ifilter

from .utils import library_macro
from ..file_types import *
from ..iterutils import iterate, uniques
from ..path import Path, Root
from ..platforms import platform_name


class CcCompiler(object):
    def __init__(self, env, lang, name, command, cflags):
        self.platform = env.platform
        self.lang = lang

        self.rule_name = self.command_var = name
        self.command = command

        self.global_args = cflags

    @property
    def flavor(self):
        return 'cc'

    @property
    def deps_flavor(self):
        return 'gcc'

    def __call__(self, cmd, input, output, deps=None, args=None):
        result = [cmd]
        result.extend(iterate(args))
        result.extend(['-c', input])
        if deps:
            result.extend(['-MMD', '-MF', deps])
        result.extend(['-o', output])
        return result

    def output_file(self, name):
        return ObjectFile(Path(name + '.o', Root.builddir), self.lang)

    def _include_dir(self, directory):
        if directory.system:
            return ['-isystem' + directory.path]
        else:
            return ['-I' + directory.path]

    def args(self, includes):
        return sum((self._include_dir(i) for i in includes), [])

    def link_args(self, name, mode):
        if mode == 'executable':
            return []
        elif mode in ['shared_library', 'static_library']:
            args = ['-fPIC']
            if self.platform.has_import_library:
                args.append('-D' + library_macro(name, mode))
            return args
        else:
            raise ValueError("unknown mode '{}'".format(mode))


class CcLinker(object):
    def __init__(self, env, lang, name, command, ldflags, ldlibs):
        self.env = env
        self.lang = lang

        self.rule_name = 'link_' + name
        self.command_var = name
        self.command = command
        self.link_var = 'ld'

        self.global_args = ldflags
        self.global_libs = ldlibs

        # Create a regular expression to extract the library name for linking
        # with -l.
        lib_formats = [r'lib(.*)\.a']
        if not self.platform.has_import_library:
            so_ext = re.escape(self.platform.shared_library_ext)
            lib_formats.append(r'lib(.*)' + so_ext)
        # XXX: Include Cygwin here too?
        if self.platform.name == 'windows':
            lib_formats.append(r'(.*)\.lib')
        self._lib_re = re.compile('(?:' + '|'.join(lib_formats) + ')$')

    def _extract_lib_name(self, library):
        basename = library.link.path.basename()
        m = self._lib_re.match(basename)
        if not m:
            raise ValueError("'{}' is not a valid library name"
                             .format(basename))

        # Get the first non-None group from the match.
        return next(ifilter( None, m.groups() ))

    @property
    def platform(self):
        return self.env.platform

    @property
    def flavor(self):
        return 'cc'

    def __call__(self, cmd, input, output, libs=None, args=None):
        result = [cmd]
        result.extend(iterate(args))
        result.extend(iterate(input))
        result.extend(iterate(libs))
        result.extend(['-o', output])
        return result

    @property
    def post_install(self):
        if self.platform.has_rpath:
            return self.env.tool('patchelf')
        return None

    @property
    def auto_link(self):
        return False

    @property
    def mode_args(self):
        return []

    def _lib_dirs(self, libraries, extra_dirs):
        dirs = uniques(chain(
            (i.path.parent() for i in iterate(libraries)
             if not isinstance(i, StaticLibrary)),
            extra_dirs
        ))
        return ['-L' + i for i in dirs]

    def _rpath(self, libraries, start):
        if self.platform.has_rpath:
            paths = uniques(i.path.parent().relpath(start) for i in libraries
                            if isinstance(i, SharedLibrary))
            if paths:
                base = '$ORIGIN'
                return ['-Wl,-rpath={}'.format(':'.join(
                    base if i == '.' else os.path.join(base, i) for i in paths
                ))]

        return []

    def args(self, libraries, extra_dirs, target):
        return ( self._lib_dirs(libraries, extra_dirs) +
                 self._rpath(libraries, target.path.parent()) )

    def _link_lib(self, library):
        if isinstance(library, WholeArchive):
            if platform_name() == 'darwin':
                return ['-Wl,-force_load', library.link.path]
            return ['-Wl,--whole-archive', library.link.path,
                    '-Wl,--no-whole-archive']
        elif isinstance(library, StaticLibrary):
            return [library.link.path]

        # If we're here, we have a SharedLibrary (or possibly just a Library
        # in the case of MinGW).
        return ['-l' + self._extract_lib_name(library)]

    def libs(self, libraries):
        return sum((self._link_lib(i) for i in libraries), [])


class CcExecutableLinker(CcLinker):
    def output_file(self, name):
        path = Path(name + self.platform.executable_ext, Root.builddir)
        return Executable(path, self.lang)


class CcSharedLibraryLinker(CcLinker):
    def output_file(self, name):
        head, tail = os.path.split(name)

        def lib(prefix='lib', suffix=''):
            return Path(os.path.join(
                head, prefix + tail + self.platform.shared_library_ext + suffix
            ), Root.builddir)

        if self.platform.has_import_library:
            dllprefix = 'cyg' if self.platform.name == 'cygwin' else 'lib'
            implib = ImportLibrary(lib(suffix='.a'), self.lang)
            return DllLibrary(lib(dllprefix), self.lang, implib)
        else:
            return SharedLibrary(lib(), self.lang)

    @property
    def mode_args(self):
        return ['-shared', '-fPIC']

    def _import_lib(self, library):
        if self.platform.has_import_library:
            return ['-Wl,--out-implib=' + library.import_lib.path]
        return []

    def args(self, libraries, extra_dirs, target):
        return (CcLinker.args(self, libraries, extra_dirs, target) +
                self._import_lib(target))


class CcPackageResolver(object):
    def __init__(self, env, lang, cmd):
        value = env.getvar('CPATH')
        include_dirs = value.split(os.pathsep) if value else []

        self.include_dirs = [i for i in uniques(chain(
            include_dirs, env.platform.include_dirs
        )) if os.path.exists(i)]

        try:
            # XXX: Will this work for cross-compilation?
            output = subprocess.check_output(
                [cmd, '-print-search-dirs'],
                universal_newlines=True
            )
            m = re.search(r'^libraries: (.*)', output, re.MULTILINE)
            system_lib_dirs = re.split(os.pathsep, m.group(1))
        except:
            system_lib_dirs = []

        value = env.getvar('LIBRARY_PATH')
        user_lib_dirs = value.split(os.pathsep) if value else []

        # XXX: Handle sysroot one day?
        all_lib_dirs = ( os.path.abspath(re.sub('^=', '', i))
                         for i in chain(user_lib_dirs, system_lib_dirs) )
        self.lib_dirs = [i for i in uniques(chain(
            all_lib_dirs, env.platform.lib_dirs
        )) if os.path.exists(i)]

        self.lang = lang
        self.platform = env.platform

    def header(self, name, search_dirs=None):
        if search_dirs is None:
            search_dirs = self.include_dirs

        for base in search_dirs:
            if os.path.exists(os.path.join(base, name)):
                return HeaderDirectory(Path(base, Root.absolute), system=True)

        raise ValueError("unable to find header '{}'".format(name))

    def library(self, name, kind='any', search_dirs=None):
        if search_dirs is None:
            search_dirs = self.lib_dirs

        libnames = []
        if kind in ('any', 'shared'):
            libname = 'lib' + name + self.platform.shared_library_ext
            if self.platform.has_import_library:
                libnames.append((libname + '.a', ImportLibrary))
            else:
                libnames.append((libname, SharedLibrary))
        if kind in ('any', 'static'):
            libnames.append(('lib' + name + '.a', StaticLibrary))

        # XXX: Include Cygwin here too?
        if self.platform.name == 'windows':
            # We don't actually know what kind of library this is. It could be
            # a static library or an import library (which we classify as a
            # kind of shared lib).
            libnames.append((name + '.lib', Library))

        for base in search_dirs:
            for libname, libkind in libnames:
                fullpath = os.path.join(base, libname)
                if os.path.exists(fullpath):
                    return libkind(Path(fullpath, Root.absolute), self.lang)

        raise ValueError("unable to find library '{}'".format(name))
