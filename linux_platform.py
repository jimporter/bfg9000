from rule import Rule

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
