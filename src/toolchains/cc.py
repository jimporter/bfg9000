import os
from collections import Iterable

from node import Node

def _lib_link_name(node):
    if isinstance(node, Node):
        return os.path.basename(node.name)
    else:
        return str(node)

def _listify(thing):
    if thing is None:
        return []
    elif isinstance(thing, Iterable) and not isinstance(thing, basestring):
        return thing
    else:
        return [thing]

def _strlistify(thing):
    return (str(i) for i in _listify(thing))

class CcCompiler(object):
    def __init__(self):
        self.command_name = os.getenv('CC', 'cc')
        self.safe_name = 'cc'

    def compile_command(self, cmd, input, output, dep=None, prevars=None,
                        postvars=None):
        result = str(cmd)
        if prevars:
            result += ' ' + ' '.join(_strlistify(prevars))
        if dep:
            result += ' -MMD -MF ' + dep
        if postvars:
            result += ' ' + ' '.join(_strlistify(postvars))
        result += ' -c {input} -o {output}'.format(
            input=input, output=output
        )
        return result

    def link_command(self, cmd, mode, input, output, libs=None, prevars=None,
                     postvars=None):
        result = str(cmd)
        if mode == 'library':
            result += ' -shared'
        if prevars:
            result += ' ' + ' '.join(_strlistify(prevars))
        result += ' ' + ' '.join(_strlistify(input))
        if libs:
            result += ' ' + self.link_libs(libs)
        if postvars:
            result += ' ' + ' '.join(_strlistify(postvars))
        result += ' -o ' + str(output)
        return result

    def library_flag(self):
        return '-fPIC'

    def link_libs(self, iterable):
        return ' '.join(('-l' + _lib_link_name(i) for i in iterable))

class CxxCompiler(CcCompiler):
    def __init__(self):
        self.command_name = os.getenv('CXX', 'c++')
        self.safe_name = 'cxx'
