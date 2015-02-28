import os
import re

from linux_platform import *
from rule import filter_rules
from languages import ext2lang

__rule_handlers__ = {}
def rule_handler(rule_name):
    def decorator(fn):
        __rule_handlers__[rule_name] = fn
        return fn
    return decorator

def write_makefile_rule(out, target, deps, commands, phony=False):
    if phony:
        out.write('.PHONY: {}\n'.format(target))
    out.write('{target}:{deps}\n'.format(
        target=target,
        deps=''.join((' ' +target_name(i) for i in deps))
    ))
    for cmd in commands:
        out.write('\t{}\n'.format(cmd))
    out.write('\n')

def write_makefile(path, targets):
    with open(os.path.join(path, 'Makefile'), 'w') as out:
        for i in targets.itervalues():
            for rule in i:
                __rule_handlers__[rule.kind](out, rule)

__var_table__ = set()
def unique_var_name(name):
    name = re.sub('/', '_', name)
    if name in __var_table__:
        i = 2
        fmt = name + '_{}'
        while True:
            name = fmt.format(i)
            if name not in __var_table__:
                break
            i += 1
    __var_table__.add(name)
    return name

__seen_compile_rules__ = set()

@rule_handler('compile')
def emit_compile(out, rule):
    base, ext = os.path.splitext(rule.attrs['file'])
    c = lang2compile[rule.attrs['lang']]
    recipe = [c['cmd'].format(input='$<', output='$@', dep='$*.d')]
    if c['depfile']:
        recipe.extend([
            "@sed -e 's/.*://' -e 's/\\$$//' < $*.d | fmt -1 | \\",
            "  sed -e 's/^ *//' -e 's/$$/:/' >> $*.d"
        ])
    if ext2lang[ext] == rule.attrs['lang']:
        if ext not in __seen_compile_rules__:
            __seen_compile_rules__.add(ext)
            write_makefile_rule(out, '%.o', ['%' + ext], recipe)
    else:
        write_makefile_rule(out, base + '.o', [rule.attrs['file']], recipe)

    if c['depfile']:
        out.write('-include {}.d\n'.format(base))

def space(s):
    if len(s):
        return ' ' + s
    else:
        return s

def emit_link(out, rule, var_prefix, command_template):
    if len(rule.attrs['files']) > 1:
        var_name = unique_var_name(
            '{}{}_OBJS'.format(var_prefix, rule.name.upper())
        )
        out.write('{} := {}\n'.format(var_name, ' '.join(
            (target_name(i) for i in rule.attrs['files'])
        )))
        files = '$({})'.format(var_name)
    else:
        files = target_name(rule.attrs['files'][0])

    write_makefile_rule(
        out,
        target_name(rule),
        rule.deps + [files] + filter_rules(rule.attrs['libs']),
        [command_template.format(
            input=files,
            libs=space(link_libs(rule.attrs['libs'])),
            output='$@'
        )]
    )

def lang(iterable):
    if any((i.attrs['lang'] == 'c++' for i in iterable)):
        return 'c++'
    else:
        return 'c'

@rule_handler('executable')
def emit_executable(out, rule):
    emit_link(out, rule, '', lang2exe[lang(rule.attrs['files'])]['cmd'])

@rule_handler('library')
def emit_library(out, rule):
    emit_link(out, rule, 'LIB', lang2so[lang(rule.attrs['files'])]['cmd'])

@rule_handler('target')
def emit_target(out, rule):
    write_makefile_rule(out, target_name(rule), rule.deps, [], phony=True)

@rule_handler('command')
def emit_command(out, rule):
    write_makefile_rule(out, target_name(rule), rule.deps, rule.attrs['cmd'],
                        phony=True)
