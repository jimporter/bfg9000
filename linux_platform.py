from rule import Rule

# Some (all?) of this should probably be tool-specific instead of
# platform-specific.

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

lang2compile = {
    'c':   {'cmd': 'gcc -MMD -MF {dep} -c {input} -o {output}',
            'depfile': True},
    'c++': {'cmd': 'g++ -MMD -MF {dep} -c {input} -o {output}',
            'depfile': True}
}

lang2exe = {
    'c':   {'cmd': 'gcc {input}{libs} -o {output}'},
    'c++': {'cmd': 'g++ {input}{libs} -o {output}'}
}

lang2so = {
    'c':   {'cmd': 'gcc -shared {input}{libs} -o {output}'},
    'c++': {'cmd': 'g++ -shared {input}{libs} -o {output}'}
}
