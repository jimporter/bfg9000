from node import Node

# This is probably platform-specific, not toolchain-specific.
def target_name(node, kind=None):
    if isinstance(node, Node):
        kind = node.kind
        name = node.name
    else:
        name = node

    if kind == 'library' or kind == 'external_library':
        return 'lib{}.so'.format(name)
    elif kind == 'object_file':
        return '{}.o'.format(name)
    else:
        return name

def target_names(iterable, kind=None):
    return ' '.join((target_name(i, kind) for i in iterable))

def lib_link_name(node):
    if isinstance(node, Node):
        return node.name
    else:
        return node

def link_libs(iterable):
    return ' '.join(('-l' + lib_link_name(i) for i in iterable))

def command_name(lang):
    return 'g++' if lang == 'c++' else 'gcc'

def compile_command(cmd, input, output, dep):
    return '{cmd} -MMD -MF {dep} -c {input} -o {output}'.format(
        cmd=cmd, input=target_name(input, 'source_file'),
        output=target_name(output, 'object_file'), dep=dep
    )

def link_command(cmd, mode, input, libs, output, prevars=None, postvars=None):
    result = cmd
    if mode == 'library':
        result += ' -shared'
    if prevars:
        result += ' ' + prevars
    result += ' ' + ' '.join(input)
    if libs:
        result += ' ' + link_libs(libs)
    if postvars:
        result += ' ' + postvars
    result += ' -o ' + output
    return result
