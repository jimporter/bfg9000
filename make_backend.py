import os
import re

from linux_platform import *
from rule import filter_rules

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

def write_makefile(out, targets):
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
    if ext not in __seen_compile_rules__:
        __seen_compile_rules__.add(ext)
        write_makefile_rule(
            out,
            '%.o',
            ['%' + ext],
            ["$(eval TEMP := $(shell mktemp $(TMPDIR)/$(notdir $*)-XXXXXX.d))",
             "g++ -MMD -MF $(TEMP) -c $< -o $@",
             "@sed -e 's|.*:|$*.o:|' < $(TEMP) > $*.d",
             "@sed -e 's/.*://' -e 's/\\$$//' < $(TEMP) | fmt -1 | \\",
             "  sed -e 's/^ *//' -e 's/$$/:/' >> $*.d",
             "@rm -f $(TEMP)"]
        )
    out.write('-include {}.d\n'.format(base))

def emit_link(out, rule, var_prefix, command_template):
    if len(rule.attrs['files']) > 0:
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
            files=files,
            libs=''.join((' -l' + lib_link_name(i) for i in rule.attrs['libs']))
        )]
    )

@rule_handler('executable')
def emit_executable(out, rule):
    emit_link(out, rule, '', 'g++ {files}{libs} -o $@')

@rule_handler('library')
def emit_library(out, rule):
    emit_link(out, rule, 'LIB', 'g++ -shared {files}{libs} -o $@')

@rule_handler('target')
def emit_target(out, rule):
    write_makefile_rule(out, target_name(rule), rule.deps, [], phony=True)

@rule_handler('command')
def emit_command(out, rule):
    write_makefile_rule(out, target_name(rule), rule.deps, rule.attrs['cmd'],
                        phony=True)
