import os
import sys

from . import *


def print_stderr_args(message):
    return [sys.executable, '-c', 'import sys; sys.stderr.write("{}")'.format(
        message.replace('"', '\\"').replace('\n', '\\n')
    )]


class TestJvmOutput(SubprocessTestCase):
    def test_jdk_8(self):
        self.assertOutput(
            ['bfg9000-jvmoutput'] + print_stderr_args(
                '[wrote RegularFileObject[foo/bar.class]]\n'
            ),
            'foo/bar.class\n'
        )

    def test_jdk_10(self):
        self.assertOutput(
            ['bfg9000-jvmoutput'] + print_stderr_args(
                '[wrote DirectoryFileObject[bad:foo/bar.class]]\n'
            ),
            os.path.join('bad', 'foo/bar.class') + '\n'
        )

    def test_jdk_11(self):
        self.assertOutput(
            ['bfg9000-jvmoutput'] + print_stderr_args(
                '[wrote foo/bar.class]\n'
            ),
            'foo/bar.class\n'
        )

    def test_scala(self):
        self.assertOutput(
            ['bfg9000-jvmoutput'] + print_stderr_args(
                "[wrote 'bar' to foo/bar.class]\n"
            ),
            'foo/bar.class\n'
        )

    def test_multiple(self):
        self.assertOutput(
            ['bfg9000-jvmoutput'] + print_stderr_args(
                '[wrote foo/bar.class]\n' +
                '[wrote baz/quux.class]\n'
            ),
            'foo/bar.class\nbaz/quux.class\n'
        )

    def test_non_verbose(self):
        self.assertOutput(
            ['bfg9000-jvmoutput', '-o', os.devnull] + print_stderr_args(
                '[wrote foo/bar.class]\n' +
                'bleep\n'
            ),
            'bleep\n'
        )

    def test_dash(self):
        self.assertOutput(
            ['bfg9000-jvmoutput', '--'] + print_stderr_args(
                '[wrote RegularFileObject[foo/bar.class]]\n'
            ),
            'foo/bar.class\n'
        )

    def test_no_args(self):
        self.assertPopen(['bfg9000-jvmoutput'], returncode=2)
        self.assertPopen(['bfg9000-jvmoutput', '--'], returncode=2)

    def test_nonexistent_command(self):
        self.assertPopen(['bfg9000-jvmoutput', 'nonexist'], returncode=66)
