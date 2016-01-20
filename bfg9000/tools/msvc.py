import os.path
from itertools import chain

from .utils import library_macro
from .. import shell
from ..file_types import *
from ..iterutils import iterate, uniques
from ..path import Root


class MsvcCompiler(object):
    def __init__(self, env, lang, name, command, cflags):
        self.platform = env.platform
        self.lang = lang

        self.rule_name = self.command_var = name
        self.command = command

        self.global_args = ['/nologo'] + cflags

    @property
    def flavor(self):
        return 'msvc'

    @property
    def deps_flavor(self):
        return 'msvc'

    def __call__(self, cmd, input, output, deps=None, args=None):
        result = [cmd]
        result.extend(iterate(args))
        if deps:
            result.append('/showIncludes')
        result.extend(['/c', input])
        result.append('/Fo' + output)
        return result

    def output_file(self, name):
        return ObjectFile(name + '.obj', Root.builddir, self.lang)

    @property
    def library_args(self):
        return []

    def include_dir(self, directory):
        return ['/I' + directory.path]

    def link_args(self, name, mode):
        if mode == 'executable':
            return []
        elif mode in ['shared_library', 'static_library']:
            return ['/D' + library_macro(name, mode)]
        else:
            raise ValueError("unknown mode '{}'".format(mode))


class MsvcLinker(object):
    def __init__(self, env, mode, lang, name, command, ldflags, ldlibs):
        self.platform = env.platform
        self.mode = mode
        self.lang = lang

        self.rule_name = self.command_var = 'link_' + name
        self.command = command
        self.link_var = 'ld'

        self.global_args = ['/nologo'] + ldflags
        self.global_libs = ldlibs

    @property
    def flavor(self):
        return 'msvc'

    def __call__(self, cmd, input, output, libs=None, args=None):
        result = [cmd]
        result.extend(iterate(args))
        result.extend(iterate(input))
        result.extend(iterate(libs))
        result.append('/OUT:' + output)
        return result

    def output_file(self, name):
        if self.mode == 'executable':
            return Executable(name + self.platform.executable_ext,
                              Root.builddir, self.lang)
        elif self.mode == 'shared_library':
            return DllLibrary(name + self.platform.shared_library_ext,
                              name + '.lib', Root.builddir, self.lang)
        else:
            raise ValueError("unknown mode '{}'".format(self.mode))

    @property
    def auto_link(self):
        return True

    @property
    def mode_args(self):
        return ['/DLL'] if self.mode == 'shared_library' else []

    def lib_dirs(self, libraries, target):
        def get_dir(lib):
            return lib.path.parent() if isinstance(lib, Library) else lib
        dirs = uniques(get_dir(i) for i in iterate(libraries))
        return ['/LIBPATH:' + i for i in dirs]

    def link_lib(self, library):
        if isinstance(library, WholeArchive):
            raise ValueError('MSVC does not support whole-archives')
        return [library.link.path.basename()]

    def import_lib(self, library):
        if self.mode != 'shared_library':
            return []
        return ['/IMPLIB:' + library.import_lib.path]


class MsvcStaticLinker(object):
    def __init__(self, env, lang, name, command):
        self.platform = env.platform
        self.mode = 'static_library'
        self.lang = lang

        self.rule_name = self.command_var = 'lib_' + name
        self.command = command
        self.link_var = 'lib'

        self.global_args = shell.split(env.getvar('LIBFLAGS', ''))

    @property
    def flavor(self):
        return 'msvc'

    def __call__(self, cmd, input, output, args=None):
        result = [cmd]
        result.extend(iterate(args))
        result.extend(iterate(input))
        result.append('/OUT:' + output)
        return result

    def output_file(self, name):
        return StaticLibrary(name + '.lib', Root.builddir, self.lang)

    @property
    def mode_args(self):
        return []


class MsvcLibFinder(object):
    def __init__(self, env, lang):
        system = env.getvar('LIB')
        system_dirs = system.split(os.pathsep) if system else []

        user = env.getvar('LIBRARY_PATH')
        user_dirs = user.split(os.pathsep) if user else []

        all_dirs = [os.path.abspath(i) for i in chain(user_dirs, system_dirs)]
        self.search_dirs = [i for i in uniques(
            chain(all_dirs, env.platform.lib_dirs)
        ) if os.path.exists(i)]

        self.lang = lang

    def __call__(self, name, kind='any', search_dirs=None):
        if search_dirs is None:
            search_dirs = self.search_dirs
        libname = name + '.lib'

        for base in search_dirs:
            fullpath = os.path.join(base, libname)
            if os.path.exists(fullpath):
                # We don't actually know what kind of library this is. It could
                # be a static library or an import library (which we classify
                # as a kind of shared lib).
                return Library(fullpath, Root.absolute, self.lang)
        raise ValueError("unable to find library '{}'".format(name))
