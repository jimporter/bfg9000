import os
import shlex

import utils

class CcCompilerBase(object):
    def __init__(self, platform_info, command, name):
        self._platform_info = platform_info
        self.command_name = command
        self.name = name
        self.command_var = name

    def command(self, cmd, input, output, dep=None, args=None):
        result = [cmd]
        result.extend(utils.listify(args))
        result.extend(['-c', input])
        if dep:
            result.extend(['-MMD', '-MF', dep])
        result.extend(['-o', output])
        return result

    def output_name(self, basename):
        return self._platform_info.object_file_name(basename)

    @property
    def library_args(self):
        return ['-fPIC']

    def include_dir(self, directory):
        return ['-I' + directory]

class CcLinkerBase(object):
    def __init__(self, mode, platform_info, command, name):
        self._mode = mode
        self._platform_info = platform_info
        self.command_name = command
        self.name = 'link_' + name
        self.command_var = name
        self.link_var = 'ld'

    def command(self, cmd, input, output, libs=None, args=None):
        result = [cmd]
        result.extend(utils.listify(args))
        result.extend(utils.listify(input))
        result.extend(utils.listify(libs))
        result.extend(['-o', output])
        return result

    def output_name(self, basename):
        if self._mode == 'shared_library':
            return self._platform_info.shared_library_name(basename)
        else:
            return self._platform_info.executable_name(basename)

    @property
    def mode_args(self):
        return ['-shared', '-fPIC'] if self._mode == 'shared_library' else []

    def lib_dir(self, directory):
        return ['-L' + directory]

    def link_lib(self, library):
        return ['-l' + library]

    def rpath(self, paths):
        rpath = ':'.join(os.path.join('$ORIGIN', i) for i in paths)
        if not rpath:
            return []
        return ["-Wl,-rpath='{}'".format(rpath)]

class CcCompiler(CcCompilerBase):
    def __init__(self, platform_info):
        CcCompilerBase.__init__(
            self, platform_info, os.getenv('CC', 'cc'), 'cc'
        )
        self.global_args = (
            shlex.split(os.getenv('CFLAGS', ''), posix=False) +
            shlex.split(os.getenv('CPPFLAGS', ''), posix=False)
        )

class CxxCompiler(CcCompilerBase):
    def __init__(self, platform_info):
        CcCompilerBase.__init__(
            self, platform_info, os.getenv('CXX', 'c++'), 'cxx'
        )
        self.global_args = (
            shlex.split(os.getenv('CXXFLAGS', ''), posix=False) +
            shlex.split(os.getenv('CPPFLAGS', ''), posix=False)
        )

class CcLinker(CcLinkerBase):
    def __init__(self, mode, platform_info):
        CcLinkerBase.__init__(
            self, mode, platform_info, os.getenv('CC', 'cc'), 'cc'
        )
        self.global_args = shlex.split(os.getenv('LDFLAGS', ''), posix=False)

class CxxLinker(CcLinkerBase):
    def __init__(self, mode, platform_info):
        CcLinkerBase.__init__(
            self, mode, platform_info, os.getenv('CXX', 'c++'), 'cxx'
        )
        self.global_args = shlex.split(os.getenv('LDFLAGS', ''), posix=False)
