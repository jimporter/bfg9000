import native
import utils

class MSVCCompiler(native.NativeCompiler):
    def __init__(self, platform_info):
        native.NativeCompiler.__init__(self, platform)
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

    @property
    def library_args(self):
        return []

    def include_dir(self, directory):
        return ['/I' + directory]

class MSVCLinker(native.NativeLinker):
    def __init__(self, platform, mode):
        native.NativeLinker.__init__(self, platform, mode)
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
