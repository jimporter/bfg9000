import json
import os.path

from ... import path
from ... import safe_str
from ... import shell
from ...iterutils import isiterable
from ...tools.common import Command

_rule_handlers = {}

filepath = path.Path('compile_commands.json')


class CompDB:
    def __init__(self, env):
        self._env = env

        self._commands = []

    def _stringify(self, thing, directory=None):
        thing = safe_str.safe_str(thing)
        if isinstance(thing, safe_str.jbos):
            return safe_str.jbos.from_iterable(
                self._stringify(i, directory) for i in thing.bits
            )
        elif isinstance(thing, path.BasePath):
            result = thing.string(self._env.base_dirs)
            if thing.root == path.Root.builddir:
                dir_str = directory.string(self._env.base_dirs)
                return os.path.relpath(result, dir_str)
            return result
        return thing

    def _stringify_arguments(self, arguments, directory=None):
        stringified = (self._stringify(i, directory) for i in
                       Command.convert_args(arguments, lambda i: i.command))
        if isinstance(arguments, shell.shell_list):
            return shell.join(stringified)
        else:
            return list(stringified)

    def append(self, *, file, directory=None, command=None, arguments=None,
               output=None):
        if (command is None) == (arguments is None):
            raise ValueError('exactly one of "command" or "arguments" must ' +
                             'be specified')

        if directory is None:
            directory = self._env.builddir
        entry = {'directory': self._stringify(directory)}

        if arguments is not None:
            arguments = self._stringify_arguments(arguments, directory)
            if isiterable(arguments):
                entry['arguments'] = arguments
            else:
                command = arguments
        if command is not None:
            entry['command'] = command

        entry['file'] = self._stringify(file, directory)
        if output is not None:
            entry['output'] = self._stringify(output, directory)
        self._commands.append(entry)

    def write(self, out):
        json.dump(self._commands, out, indent=2)


def rule_handler(*args):
    def decorator(fn):
        for i in args:
            _rule_handlers[i] = fn
        return fn
    return decorator


def write(env, build_inputs):
    buildfile = CompDB(env)
    for e in build_inputs.edges():
        if type(e) in _rule_handlers:
            _rule_handlers[type(e)](e, build_inputs, buildfile, env)

    with open(filepath.string(env.base_dirs), 'w') as out:
        buildfile.write(out)
