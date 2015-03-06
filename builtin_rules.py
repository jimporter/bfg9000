from builtins import builtin
from languages import ext2lang
import os
import rule

@builtin
@rule.rule
def object_file(file, lang=None):
    if lang is None:
        lang = ext2lang.get( os.path.splitext(file)[1] )
    return {'file': file, 'lang': lang}

@builtin
def object_files(files, lang=None):
    return [object_file(os.path.splitext(f)[0], file=f, lang=lang)
            for f in files]

@builtin
@rule.rule
def executable(files, libs=None, lang=None):
    # XXX: Allow pre-built objects?
    return {'files': object_files(files=files, lang=lang), 'libs': libs or []}

@builtin
@rule.rule
def library(files, libs=None, lang=None):
    # XXX: Allow pre-built objects?
    return {'files': object_files(files=files, lang=lang), 'libs': libs or []}

@builtin
@rule.rule
def target():
    return {}

@builtin
@rule.rule
def command(cmd):
    return {'cmd': cmd}
