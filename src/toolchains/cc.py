from node import Node
from platform import target_name

def _lib_link_name(node):
    if isinstance(node, Node):
        return node.name
    else:
        return str(node)

def _target_name_or_str(thing):
    if isinstance(thing, Node):
        return target_name(thing)
    else:
        return str(thing)

class CcCompiler(object):
    def command_name(self, lang):
        if not isinstance(lang, basestring):
            is_cxx = any(i == 'c++' for i in lang)
        else:
            is_cxx = lang == 'c++'

        if is_cxx:
            return ('c++', 'cxx')
        else:
            return ('cc', 'cc')

    def compile_command(self, cmd, input, output, dep=None, prevars=None):
        result = cmd
        if prevars:
            result += ' ' + prevars
        if dep:
            result += ' -MMD -MF ' + dep
        result += ' -c {input} -o {output}'.format(
            input=_target_name_or_str(input),
            output=_target_name_or_str(output)
        )
        return result

    def link_command(self, cmd, mode, input, output, libs=None, prevars=None,
                     postvars=None):
        result = cmd
        if mode == 'library':
            result += ' -shared'
        if prevars:
            result += ' ' + prevars
        result += ' ' + ' '.join(input)
        if libs:
            result += ' ' + self.link_libs(libs)
        if postvars:
            result += ' ' + postvars
        result += ' -o ' + output
        return result

    def library_flag(self):
        return '-fPIC'

    def link_libs(self, iterable):
        return ' '.join(('-l' + _lib_link_name(i) for i in iterable))
