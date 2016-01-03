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
            return DllLibrary(name + self.platform.executable_ext,
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
