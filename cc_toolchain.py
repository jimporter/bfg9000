from rule import Rule

# This is probably platform-specific, not toolchain-specific.
def target_name(rule):
    if isinstance(rule, Rule):
        if rule.kind == 'library':
            return 'lib{}.so'.format(rule.name)
        elif rule.kind == 'compile':
            return '{}.o'.format(rule.name)
        else:
            return rule.name
    else:
        return rule

def lib_link_name(rule):
    if isinstance(rule, Rule):
        return rule.name
    else:
        return rule

def link_libs(iterable):
    return ' '.join(('-l' + lib_link_name(i) for i in iterable))

def compile_command(lang, input, output, dep):
    return '{cmd} -MMD -MF {dep} -c {input} -o {output}'.format(
        cmd='g++' if lang == 'c++' else 'gcc',
        input=input, output=output, dep=dep
    )

def link_command(lang, mode, input, libs, output, prevars=None, postvars=None):
    # TODO: support static libraries
    cmd = 'g++' if lang == 'c++' else 'gcc'
    if mode == 'library':
        cmd += ' -shared'

    result = cmd
    if prevars:
        result += ' ' + prevars
    result += ' ' + input
    if libs:
        result += ' ' + link_libs(libs)
    if postvars:
        result += ' ' + postvars
    result += ' -o ' + output
    return result
