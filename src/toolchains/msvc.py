import utils

class MSVCCompiler(object):
    def __init__(self, platform_info):
        self._platform_info = platform_info
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

    def output_name(self, basename):
        return self._platform_info.object_file_name(basename)

    @property
    def library_args(self):
        return []

    def include_dir(self, directory):
        return ['/I' + directory]

class MSVCLinker(object):
    def __init__(self, mode, platform_info):
        self.mode = mode
        self._platform_info = platform_info
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

    def output_name(self, basename):
        if self.mode == 'shared_library':
            return self._platform_info.shared_library_name(basename)
        else:
            return self._platform_info.executable_name(basename)

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
