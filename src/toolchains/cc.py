import os

import utils
from build_inputs import Node

def _lib_link_name(node):
    if isinstance(node, Node):
        return os.path.basename(node.name)
    else:
        return str(node)

class CcCompiler(object):
    def __init__(self):
        self.command_name = os.getenv('CC', 'cc')
        self.command_var = 'cc'
        self.name = 'cc'

    def command(self, cmd, input, output, dep=None, pre_args=None,
                post_args=None):
        result = str(cmd)
        if pre_args:
            result += ' ' + ' '.join(utils.strlistify(pre_args))
        if dep:
            result += ' -MMD -MF ' + dep
        if post_args:
            result += ' ' + ' '.join(utils.strlistify(post_args))
        result += ' -c {input} -o {output}'.format(
            input=input, output=output
        )
        return result

    @property
    def library_args(self):
        return ['-fPIC']

    def include_dirs(self, iterable):
        return ' '.join('-I' + i for i in iterable)

class CcLinker(object):
    def __init__(self, mode):
        self.command_name = os.getenv('CC', 'cc')
        self.command_var = 'cc'
        self._mode = mode
        self.name = 'link_cc'

    def command(self, cmd, input, output, libs=None, pre_args=None,
                post_args=None):
        result = str(cmd)
        if pre_args:
            result += ' ' + ' '.join(utils.strlistify(pre_args))
        result += ' ' + ' '.join(utils.strlistify(input))
        if libs:
            result += ' ' + self.link_libs(libs)
        if post_args:
            result += ' ' + ' '.join(utils.strlistify(post_args))
        result += ' -o ' + str(output)
        return result

    @property
    def always_args(self):
        return ['-shared', '-fPIC'] if self._mode == 'shared_library' else []

    def link_libs(self, iterable):
        return ' '.join('-l' + _lib_link_name(i) for i in iterable)

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
