import os.path
import re
import subprocess
from itertools import chain
from six.moves import filter as ifilter

from .utils import library_macro
from ..file_types import *
from ..iterutils import iterate, listify, uniques
from ..path import Root
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
        return ObjectFile(name + '.o', Root.builddir, self.lang)

    def include_dir(self, directory):
        if directory.system:
            return ['-isystem' + directory.path]
        else:
            return ['-I' + directory.path]

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
    def __init__(self, env, mode, lang, name, command, ldflags, ldlibs):
        self.env = env
        self.mode = mode
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

    def output_file(self, name):
        if self.mode == 'executable':
            return Executable(
                name + self.platform.executable_ext, Root.builddir, self.lang
            )
        elif self.mode == 'shared_library':
            head, tail = os.path.split(name)

            def lib(prefix='lib'):
                return os.path.join(
                    head, prefix + tail + self.platform.shared_library_ext
                )

            if self.platform.has_import_library:
                dllprefix = 'cyg' if self.platform.name == 'cygwin' else 'lib'
                return DllLibrary(lib(dllprefix), lib() + '.a', Root.builddir,
                                  self.lang)
            else:
                return SharedLibrary(lib(), Root.builddir, self.lang)
        else:
            raise ValueError("unknown mode '{}'".format(self.mode))

    @property
    def mode_args(self):
        return ['-shared', '-fPIC'] if self.mode == 'shared_library' else []

    def lib_dirs(self, libraries, target):
        def get_dir(lib):
            return lib.path.parent() if isinstance(lib, Library) else lib

        libraries = listify(libraries)
        dirs = uniques(get_dir(i) for i in iterate(libraries)
                       if not isinstance(i, StaticLibrary))
        result = ['-L' + i for i in dirs]

        if self.platform.has_rpath:
            start = target.path.parent()
            paths = uniques(i.path.parent().relpath(start) for i in libraries
                            if isinstance(i, SharedLibrary))
            if paths:
                base = '$ORIGIN'
                result.append('-Wl,-rpath={}'.format( ':'.join(
                    base if i == '.' else os.path.join(base, i) for i in paths
                ) ))

        return result

    def link_lib(self, library):
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

    def import_lib(self, library):
        if self.platform.has_import_library and self.mode == 'shared_library':
            return ['-Wl,--out-implib=' + library.import_lib.path]
        return []


class CcLibFinder(object):
    def __init__(self, env, lang, cmd):
        try:
            # XXX: Will this work for cross-compilation?
            output = subprocess.check_output(
                [cmd, '-print-search-dirs'],
                universal_newlines=True
            )
            m = re.search(r'^libraries: (.*)', output, re.MULTILINE)
            system_dirs = re.split(os.pathsep, m.group(1))
        except:
            system_dirs = []

        value = env.getvar('LIBRARY_PATH')
        user_dirs = value.split(os.pathsep) if value else []

        # XXX: Handle sysroot one day?
        all_dirs = ( os.path.abspath(re.sub('^=', '', i))
                     for i in chain(user_dirs, system_dirs) )
        self.search_dirs = [i for i in uniques(
            chain(all_dirs, env.platform.lib_dirs)
        ) if os.path.exists(i)]

        self.lang = lang
        self.platform = env.platform

    def __call__(self, name, kind='any', search_dirs=None):
        if search_dirs is None:
            search_dirs = self.search_dirs

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
            for name, lib_kind in libnames:
                fullpath = os.path.join(base, name)
                if os.path.exists(fullpath):
                    return lib_kind(fullpath, Root.absolute, self.lang)
        raise ValueError("unable to find library '{}'".format(name))
