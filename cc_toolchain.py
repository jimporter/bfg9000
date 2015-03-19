from node import Node

# This is probably platform-specific, not toolchain-specific.
def target_name(node):
    if node.kind == 'library' or node.kind == 'external_library':
        return 'lib{}.so'.format(node.name)
    elif node.kind == 'object_file':
        return '{}.o'.format(node.name)
    else:
        return node.name

def target_name_or_str(thing):
    if isinstance(thing, Node):
        return target_name(thing)
    else:
        return str(thing)

def lib_link_name(node):
    if isinstance(node, Node):
        return node.name
    else:
        return node

def link_libs(iterable):
    return ' '.join(('-l' + lib_link_name(i) for i in iterable))

def command_name(lang):
    return 'g++' if lang == 'c++' else 'gcc'

def compile_command(cmd, input, output, dep=None, prevars=None):
    result = cmd
    if prevars:
        result += ' ' + prevars
    if dep:
        result += ' -MMD -MF ' + dep
    result += ' -c {input} -o {output}'.format(
        input=target_name_or_str(input),
        output=target_name_or_str(output)
    )
    return result

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
