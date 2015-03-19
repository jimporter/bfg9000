import os

from builtins import builtin
from languages import ext2lang
import node

@builtin
@node.rule
def object_file(file, lang=None, options=None):
    if lang is None:
        lang = ext2lang.get( os.path.splitext(file)[1] )
    return {'file': node.nodeify(file, 'source_file'), 'lang': lang,
            'options': options}

@builtin
def object_files(files, lang=None, options=None):
    return [object_file(os.path.splitext(f)[0], file=f, lang=lang,
                        options=options) for f in files]

@builtin
@node.rule
def executable(files, libs=None, lang=None, compile_options=None,
               link_options=None):
    # XXX: Allow pre-built objects?
    return {'files': object_files(files=files, lang=lang,
                                  options=compile_options),
            'libs': node.nodeify_list(libs or [], 'external_library'),
            'compile_options': compile_options,
            'link_options': link_options}

@builtin
@node.rule
def library(files, libs=None, lang=None, compile_options=None,
            link_options=None):
    # XXX: Allow pre-built objects?
    return {'files': object_files(files=files, lang=lang,
                                  options=compile_options),
            'libs': node.nodeify_list(libs or [], 'external_library'),
            'compile_options': compile_options,
            'link_options': link_options}

@builtin
@node.rule
def alias():
    return {}

@builtin
@node.rule
def command(cmd):
    return {'cmd': cmd}
