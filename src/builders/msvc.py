import os

import utils
from file_types import *

class MSVCCompiler(object):
    def __init__(self, platform):
        self.platform = platform
        self.command_name = 'cl'
        self.name = 'cxx'
        self.command_var = 'cxx'
        self.global_args = [] # TODO

    def command(self, cmd, input, output, dep=None, args=None):
        result = [cmd]
        result.extend(utils.iterate(args))
        result.extend(['/c', input])
        # TODO: add depfile stuff
        result.append('/Fo' + output)
        return result

    def output_file(self, name, lang):
        return ObjectFile(name + '.obj', Path.builddir, lang)

    @property
    def library_args(self):
        return []

    def include_dir(self, directory):
        return ['/I' + directory.path.local_path()]

class MSVCLinker(object):
    def __init__(self, platform, mode):
        self.platform = platform
        self.mode = mode
        self.command_name = 'link'
        self.name = 'link'
        self.command_var = 'link'
        self.link_var = 'ld'
        self.global_args = [] # TODO
        self.global_libs = [] # TODO

    def command(self, cmd, input, output, libs=None, args=None):
        result = [cmd]
        result.extend(utils.iterate(args))
        result.extend(utils.iterate(input))
        result.extend(utils.iterate(libs))
        result.append('/OUT:' + output)
        return result

    def output_file(self, name):
        if self.mode == 'executable':
            return Executable(
                name + self.platform.executable_ext, Path.builddir
            )
        elif self.mode == 'shared_library':
            libname = os.path.basename(name)
            ext = self.platform.shared_library_ext
            return (
                SharedLibrary(libname, name + '.lib', Path.builddir),
                DynamicLibrary(libname, name + ext, Path.builddir),
            )
        else:
            raise ValueError('unknown mode "{}"'.format(self.mode))

    @property
    def mode_args(self):
        return ['/DLL'] if self.mode == 'shared_library' else []

    def lib_dirs(self, libraries):
        dirs = set(i.path.parent().local_path() for i in libraries)
        return ['/LIBPATH:' + i for i in dirs]

    def link_lib(self, library):
        return [library.path.basename()]

    def rpath(self, paths):
        return []

class MSVCStaticLinker(object):
    def __init__(self, platform):
        self.platform = platform
        self.mode = 'static_library'
        self.command_name = 'lib'
        self.name = 'lib'
        self.command_var = 'lib'
        self.link_var = 'lib'
        self.global_args = [] # TODO

    def command(self, cmd, input, output, args=None):
        result = [cmd]
        result.extend(utils.iterate(args))
        result.extend(utils.iterate(input))
        result.append('/OUT:' + output)
        return result

    def output_file(self, name):
        libname = os.path.basename(name)
        return StaticLibrary(libname, name + '.lib', Path.builddir)

    @property
    def mode_args(self):
        return []
