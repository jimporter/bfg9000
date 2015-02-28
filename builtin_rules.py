from builtins import builtin
import os
import rule

@builtin
@rule.rule
def compile(file):
    return {'file': file}

@builtin
def compile_all(files):
    return [compile(os.path.splitext(f)[0], file=f) for f in files]

@builtin
@rule.rule
def executable(files, libs=None):
    # XXX: Allow pre-built objects?
    return {'files': compile_all(files), 'libs': libs or []}

@builtin
@rule.rule
def library(files, libs=None):
    # XXX: Allow pre-built objects?
    return {'files': compile_all(files), 'libs': libs or []}

@builtin
@rule.rule
def target():
    return {'phony': True}

@builtin
@rule.rule
def command(cmd):
    return {'cmd': cmd, 'phony': True}
