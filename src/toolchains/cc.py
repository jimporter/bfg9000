import os
import shlex

import utils

class CcCompiler(object):
    def __init__(self):
        self.command_name = os.getenv('CC', 'cc')
        self.command_var = 'cc'
        self.name = 'cc'

        self.global_args = (
            shlex.split(os.getenv('CFLAGS', ''), posix=False) +
            shlex.split(os.getenv('CPPFLAGS', ''), posix=False)
        )

    def command(self, cmd, input, output, dep=None, args=None):
        result = [cmd]
        result.extend(utils.listify(args))
        result.extend(['-c', input])
        if dep:
            result.extend(['-MMD', '-MF', dep])
        result.extend(['-o', output])
        return result

    @property
    def library_args(self):
        return ['-fPIC']

    def include_dir(self, directory):
        return ['-I' + directory]

class CcLinker(object):
    def __init__(self, mode):
        self.command_name = os.getenv('CC', 'cc')
        self.command_var = 'cc'
        self.link_var = 'ld'
        self._mode = mode
        self.name = 'link_cc'

        self.global_compile_args = (
            shlex.split(os.getenv('CFLAGS', ''), posix=False) +
            shlex.split(os.getenv('CPPFLAGS', ''), posix=False)
        )
        self.global_link_args = shlex.split(os.getenv('LDFLAGS', ''),
                                            posix=False)

    def command(self, cmd, input, output, compile_args=None, link_args=None):
        result = [cmd]
        result.extend(utils.listify(compile_args))
        result.extend(utils.listify(input))
        result.extend(utils.listify(link_args))
        result.extend(['-o', output])
        return result

    @property
    def mode_args(self):
        return ['-shared', '-fPIC'] if self._mode == 'shared_library' else []

    def link_lib(self, library):
        return ['-l' + library]

class CxxCompiler(CcCompiler):
    def __init__(self):
        self.command_name = os.getenv('CXX', 'c++')
        self.command_var = 'cxx'
        self.name = 'cxx'

        self.global_args = (
            shlex.split(os.getenv('CXXFLAGS', ''), posix=False) +
            shlex.split(os.getenv('CPPFLAGS', ''), posix=False)
        )

class CxxLinker(CcLinker):
    def __init__(self, mode):
        self.command_name = os.getenv('CXX', 'c++')
        self.command_var = 'cxx'
        self.link_var = 'ld'
        self._mode = mode
        self.name = 'link_cxx'

        self.global_compile_args = (
            shlex.split(os.getenv('CXXFLAGS', ''), posix=False) +
            shlex.split(os.getenv('CPPFLAGS', ''), posix=False)
        )
        self.global_link_args = shlex.split(os.getenv('LDFLAGS', ''),
                                            posix=False)
