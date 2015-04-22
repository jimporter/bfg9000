import os

import utils

class CcCompiler(object):
    def __init__(self):
        self.command_name = os.getenv('CC', 'cc')
        self.command_var = 'cc'
        self.name = 'cc'

    def command(self, cmd, input, output, dep=None, pre_args=None,
                post_args=None):
        result = [str(cmd)]
        if pre_args:
            result.extend(utils.strlistify(pre_args))
        if dep:
            result.extend(['-MMD', '-MF', dep])
        if post_args:
            result.extend(utils.strlistify(post_args))
        result.extend(['-c', str(input), '-o', str(output)])
        return ' '.join(result)

    @property
    def library_args(self):
        return ['-fPIC']

    def include_dir(self, directory):
        return ['-I' + directory]

class CcLinker(object):
    def __init__(self, mode):
        self.command_name = os.getenv('CC', 'cc')
        self.command_var = 'cc'
        self._mode = mode
        self.name = 'link_cc'

    def command(self, cmd, input, output, libs=None, pre_args=None,
                post_args=None):
        result = [str(cmd)]
        if pre_args:
            result.extend(utils.strlistify(pre_args))
        result.extend(utils.strlistify(input))
        if libs:
            result.append(self.link_libs(libs))
        if post_args:
            result.extend(utils.strlistify(post_args))
        result.extend(['-o', str(output)])
        return ' '.join(result)

    @property
    def always_args(self):
        return ['-shared', '-fPIC'] if self._mode == 'shared_library' else []

    def link_lib(self, library):
        return ['-l' + library]

class CxxCompiler(CcCompiler):
    def __init__(self):
        self.command_name = os.getenv('CXX', 'c++')
        self.command_var = 'cxx'
        self.name = 'cxx'

class CxxLinker(CcLinker):
    def __init__(self, mode):
        self.command_name = os.getenv('CXX', 'c++')
        self.command_var = 'cxx'
        self._mode = mode
        self.name = 'link_cxx'
