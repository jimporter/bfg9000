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
        return file_types.ObjectFile(name + '.obj', Path.builddir, lang)

    @property
    def library_args(self):
        return []

    def include_dir(self, directory):
        return ['/I' + directory]

class MSVCLinker(object):
    def __init__(self, platform, mode):
        self.platform = platform
        self.mode = mode
        self.command_name = 'link'
        self.name = 'link'
        self.command_var = 'link'
        self.link_var = 'ld'
        self.global_args = [] # TODO

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
            ext = self.platform.shared_library_ext
            return (
                SharedLibrary(tail, name + '.lib', Path.builddir),
                DynamicLibrary(tail, name + ext, Path.builddir),
            )
        else:
            # TODO: Handle static libs (does this need to use a different
            # command?)
            raise RuntimeError('unknown mode "{}"'.format(self.mode))

    @property
    def mode_args(self):
        # TODO: Handle static libs (does this need to use a different command?)
        return ['/DLL'] if self.mode == 'shared_library' else []

    def lib_dir(self, directory):
        return ['/LIBPATH:' + directory]

    def link_lib(self, library):
        # TODO: Emit the actual filename for the library
        return [library]

    def rpath(self, paths):
        return []
