import subprocess
from contextlib import contextmanager
from unittest import mock


@contextmanager
def mock_uname(*, os=None, machine=None, lsb=None):
    def the_mock(cmd, *args, **kwargs):
        if cmd == ['uname', '-o'] and os:
            output = os
        elif cmd == ['uname', '-m'] and machine:
            output = machine
        elif cmd == ['lsb_release', '-is'] and lsb:
            output = lsb
        else:
            raise ValueError('unexpected command {}'.format(cmd))
        if isinstance(output, Exception):
            raise output
        return subprocess.CompletedProcess(cmd, 0, output)

    with mock.patch('subprocess.run', the_mock):
        yield
