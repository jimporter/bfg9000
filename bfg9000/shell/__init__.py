import os
import subprocess
from enum import Enum

from .list import shell_list  # noqa
from ..iterutils import listify
from ..path import BasePath, Path
from ..platforms import platform_name
from ..safe_str import jbos, safe_str

windows_names = ('winnt', 'win9x', 'msdos')

if platform_name() in windows_names:
    from .windows import *  # noqa
else:
    from .posix import *  # noqa

Mode = Enum('Mode', ['normal', 'pipe', 'stdout', 'devnull'])
CalledProcessError = subprocess.CalledProcessError


def which(names, env=os.environ, base_dirs=None, resolve=False,
          kind='executable'):
    names = listify(names)
    if len(names) == 0:
        raise TypeError('must supply at least one name')

    paths = env.get('PATH', os.defpath).split(os.pathsep)
    exts = ['']
    if platform_name() in windows_names + ('cygwin',) and env.get('PATHEXT'):
        exts.extend(env.get('PATHEXT', '').split(os.pathsep))

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

    def conv(mode):
        return ({Mode.normal : None,
                 Mode.pipe   : subprocess.PIPE,
                 Mode.stdout : subprocess.STDOUT,
                 Mode.devnull: subprocess.DEVNULL}).get(mode, mode)

    proc = subprocess.Popen(
        args, universal_newlines=True, shell=shell, env=env,
        stdout=conv(stdout), stderr=conv(stderr)
    )
    output = proc.communicate()
    if not (returncode == 'any' or
            (returncode == 'fail' and proc.returncode != 0) or
            proc.returncode in listify(returncode)):
        raise CalledProcessError(proc.returncode, args)

    if stdout == Mode.pipe:
        if stderr == Mode.pipe:
            return output
        return output[0]
    return output[1]
