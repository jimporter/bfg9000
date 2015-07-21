import os

from .. import shell
from ..file_types import *
from ..iterutils import iterate, uniques
from ..path import Root

class MSVCCompiler(object):
    def __init__(self, env):
        self.platform = env.platform
        self.command_name = 'cl'
        self.name = 'cxx'
        self.command_var = 'cxx'
        self.global_args = (
            shell.split(env.getvar('CXXFLAGS', '')) +
            shell.split(env.getvar('CPPFLAGS', ''))
        )

    def command(self, cmd, input, output, deps=None, args=None):
        result = [cmd]
        result.extend(iterate(args))
        if deps:
            result.append('/showIncludes')
        result.extend(['/c', input])
        result.append('/Fo' + output)
        return result

    def output_file(self, name, lang):
        return ObjectFile(name + '.obj', Root.builddir, lang)

    @property
    def deps_flavor(self):
        return 'msvc'

    @property
    def library_args(self):
        return []

    def include_dir(self, directory):
        return ['/I' + directory.path]

class MSVCLinker(object):
    def __init__(self, env, mode):
        self.platform = env.platform
        self.mode = mode
        self.command_name = 'link'
        self.name = 'link'
        self.command_var = 'link'
        self.link_var = 'ld'
        self.global_args = shell.split(env.getvar('LDFLAGS', ''))
        self.global_libs = shell.split(env.getvar('LDLIBS', ''))

    def command(self, cmd, input, output, libs=None, args=None):
        result = [cmd]
        result.extend(iterate(args))
        result.extend(iterate(input))
        result.extend(iterate(libs))
        result.append('/OUT:' + output)
        return result

    def output_file(self, name):
        if self.mode == 'executable':
            return Executable(
                name + self.platform.executable_ext, Root.builddir
            )
        elif self.mode == 'shared_library':
            ext = self.platform.shared_library_ext
            dll = DllLibrary(name + ext, Root.builddir)
            return SharedLibrary(name + '.lib', Root.builddir, dll)
        else:
            raise ValueError("unknown mode '{}'".format(self.mode))

    @property
    def mode_args(self):
        return ['/DLL'] if self.mode == 'shared_library' else []

    def lib_dirs(self, libraries):
        dirs = uniques(i.path.parent() for i in libraries)
        return ['/LIBPATH:' + i for i in dirs]

    def link_lib(self, library):
        return [library.path.basename()]

    def import_lib(self, library):
        if self.mode != 'shared_library':
            return []
        return ['/IMPLIB:' + library.path]

    def rpath(self, libraries, start):
        return []

class MSVCStaticLinker(object):
    def __init__(self, env):
        self.platform = env.platform
        self.mode = 'static_library'
        self.command_name = 'lib'
        self.name = 'lib'
        self.command_var = 'lib'
        self.link_var = 'lib'
        self.global_args = shell.split(env.getvar('LIBFLAGS', ''))

    def command(self, cmd, input, output, args=None):
        result = [cmd]
        result.extend(iterate(args))
        result.extend(iterate(input))
        result.append('/OUT:' + output)
        return result

    def output_file(self, name):
        return StaticLibrary(name + '.lib', Root.builddir)

    @property
    def mode_args(self):
        return []