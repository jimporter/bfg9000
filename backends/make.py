import os
import re

import cc_toolchain
from rule import filter_rules
from languages import ext2lang

__rule_handlers__ = {}
def rule_handler(rule_name):
    def decorator(fn):
        __rule_handlers__[rule_name] = fn
        return fn
    return decorator

def write(path, targets):
    with open(os.path.join(path, 'Makefile'), 'w') as out:
        for t in targets:
            __rule_handlers__[t.kind](out, t)

def write_rule(out, target, deps, commands, phony=False):
    if phony:
        out.write('.PHONY: {}\n'.format(target))
    out.write('{target}:{deps}\n'.format(
        target=target,
        deps=''.join((' ' + cc_toolchain.target_name(i) for i in deps))
    ))
    for cmd in commands:
        out.write('\t{}\n'.format(cmd))
    out.write('\n')

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

@rule_handler('object_file')
def emit_object_file(out, rule):
    base, ext = os.path.splitext(rule.attrs['file'])
    recipe = [
        cc_toolchain.compile_command(
            lang=rule.attrs['lang'], input='$<', output='$@', dep='$*.d'
        ),
        "@sed -e 's/.*://' -e 's/\\$$//' < $*.d | fmt -1 | \\",
        "  sed -e 's/^ *//' -e 's/$$/:/' >> $*.d"
    ]

    if ext2lang[ext] == rule.attrs['lang']:
        if ext not in __seen_compile_rules__:
            __seen_compile_rules__.add(ext)
            write_rule(out, '%.o', ['%' + ext], recipe)
    else:
        write_rule(out, base + '.o', [rule.attrs['file']], recipe)

    out.write('-include {}.d\n'.format(base))

def lang(iterable):
    if any((i.attrs['lang'] == 'c++' for i in iterable)):
        return 'c++'
    else:
        return 'c'

def emit_link(out, rule, mode, var_prefix):
    if len(rule.attrs['files']) > 1:
        var_name = unique_var_name(
            '{}{}_OBJS'.format(var_prefix, rule.name.upper())
        )
        out.write('{} := {}\n'.format(var_name, ' '.join(
            (cc_toolchain.target_name(i) for i in rule.attrs['files'])
        )))
        files = '$({})'.format(var_name)
    else:
        files = cc_toolchain.target_name(rule.attrs['files'][0])

    write_rule(
        out,
        cc_toolchain.target_name(rule),
        rule.deps + [files] + filter_rules(rule.attrs['libs']),
        [cc_toolchain.link_command(
            lang=lang(rule.attrs['files']), mode=mode, input=files,
            libs=rule.attrs['libs'], output='$@'
        )]
    )

@rule_handler('executable')
def emit_executable(out, rule):
    emit_link(out, rule, 'executable', '')

@rule_handler('library')
def emit_library(out, rule):
    emit_link(out, rule, 'library', 'LIB')

@rule_handler('target')
def emit_target(out, rule):
    write_rule(out, cc_toolchain.target_name(rule), rule.deps, [],
               phony=True)

@rule_handler('command')
def emit_command(out, rule):
    write_rule(out, cc_toolchain.target_name(rule), rule.deps,
               rule.attrs['cmd'], phony=True)
