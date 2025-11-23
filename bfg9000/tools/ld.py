import re

from .. import shell
from ..versioning import detect_version
from ..path import abspath


class LdLinker:
    def __init__(self, builder, env, command, version_output):
        self.builder = builder
        self.env = env
        self.command = command
        # Currently, if we're constructing this object, we know the command has
        # been found.
        self.found = True

        version_output = version_output or ''
        if 'GNU ld' in version_output:
            self.brand = 'bfd'
            self.version = detect_version(version_output)
        elif 'GNU gold' in version_output:
            self.brand = 'gold'
            self.version = detect_version(version_output, post='$', flags=re.M)
        elif 'LLD' in version_output:
            self.brand = 'lld'
            self.version = detect_version(version_output)
        elif '@(#)PROGRAM:ld' in version_output:
            self.brand = 'apple'
            self.version = detect_version(version_output)
        else:
            self.brand = 'unknown'
            self.version = None

    @staticmethod
    def call_command(env, command):
        for args in (['--version'], ['-v']):
            try:
                return env.execute(command + args, stdout=shell.Mode.pipe,
                                   stderr=shell.Mode.stdout)
            except shell.CalledProcessError:
                pass
        return None

    @property
    def lang(self):
        return self.builder.lang

    @property
    def family(self):
        return self.builder.family

    @property
    def flavor(self):
        return 'ld'

    def search_dirs(self, sysroot='/', strict=False):
        try:
            output = self.env.execute(
                self.command + ['--verbose'], stdout=shell.Mode.pipe,
                stderr=shell.Mode.devnull
            )
            search_dirs = [i.group(1) for i in re.finditer(
                r'SEARCH_DIR\("((?:[^"\\]|\\.)*)"\)', output)
            ]
            return [abspath(sysroot.rstrip('/') + i[1:] if i[0] == '=' else i)
                    for i in search_dirs]
        except (OSError, shell.CalledProcessError):
            if strict:
                raise
            return []
