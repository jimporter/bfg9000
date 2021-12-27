import os
import subprocess
from enum import Enum

from .. import iterutils
from .list import shell_list  # noqa: F401
from ..path import BasePath, Path
from ..platforms.host import platform_info
from ..safe_str import jbos, safe_str

if platform_info().family == 'windows':
    from .windows import *  # noqa: F401
else:
    from .posix import *  # noqa: F401

CalledProcessError = subprocess.CalledProcessError


class Mode(Enum):
    normal = None
    pipe = subprocess.PIPE
    stdout = subprocess.STDOUT
    devnull = subprocess.DEVNULL


def split_paths(s, sep=os.pathsep):
    if s is None:
        return []
    return [i for i in s.split(sep) if i]


def join_paths(paths, sep=os.pathsep):
    return sep.join(paths)


def which(names, env=os.environ, base_dirs=None, resolve=False,
          kind='executable'):
    names = iterutils.listify(names)
    if len(names) == 0:
        raise TypeError('must supply at least one name')

    paths = split_paths(env.get('PATH', os.defpath))
    exts = ['']
    if platform_info().has_path_ext:
        exts.extend(split_paths(env.get('PATHEXT', '')))

    for name in names:
        name = listify(name)
        check = (name[0].string(base_dirs) if isinstance(name[0], Path)
                 else name[0])
        if os.path.isabs(check):
            fullpaths = [check]
        else:
            search = ['.'] if os.path.dirname(check) else paths
            fullpaths = [os.path.normpath(os.path.join(path, check))
                         for path in search]

        for fullpath in fullpaths:
            for ext in exts:
                withext = fullpath + ext
                if os.path.exists(withext):
                    return [withext] + name[1:] if resolve else name

    raise IOError('unable to find {kind}{filler} {names}'.format(
        kind=kind, filler='; tried' if len(names) > 1 else '',
        names=', '.join('{!r}'.format(i) for i in names)
    ))


def convert_args(args, base_dirs=None):
    def convert(s):
        s = safe_str(s)
        if isinstance(s, BasePath):
            return s.string(base_dirs)
        elif isinstance(s, jbos):
            return ''.join(convert(i) for i in s.bits)
        else:
            return s

    return [convert(i) for i in args]


def execute(args, *, shell=False, env=None, base_dirs=None, stdout=Mode.normal,
            stderr=Mode.normal, returncode=0):
    if not shell:
        args = convert_args(args, base_dirs)

    def conv_mode(mode):
        return mode.value if isinstance(mode, Mode) else mode

    proc = subprocess.run(
        args, universal_newlines=True, shell=shell, env=env,
        stdout=conv_mode(stdout), stderr=conv_mode(stderr)
    )
    if not (returncode == 'any' or
            (returncode == 'fail' and proc.returncode != 0) or
            proc.returncode in iterutils.listify(returncode)):
        raise CalledProcessError(proc.returncode, proc.args, proc.stdout,
                                 proc.stderr)

    if stdout == Mode.pipe:
        if stderr == Mode.pipe:
            return proc.stdout, proc.stderr
        return proc.stdout
    return proc.stderr
