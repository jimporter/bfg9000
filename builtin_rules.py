from builtins import builtin
from languages import ext2lang
import os
import rule

@builtin
@rule.rule
def compile(file, lang=None):
    if lang is None:
        lang = ext2lang.get( os.path.splitext(file)[1] )
    return {'file': file, 'lang': lang}

@builtin
def compile_all(files, lang=None):
    return [compile(os.path.splitext(f)[0], file=f, lang=lang) for f in files]

@builtin
@rule.rule
def executable(files, libs=None, lang=None):
    # XXX: Allow pre-built objects?
    return {'files': compile_all(files=files, lang=lang), 'libs': libs or []}

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
