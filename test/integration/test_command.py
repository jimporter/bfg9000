import os.path
import re

from . import *


class TestCommand(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '07_commands'), *args, **kwargs
        )

    def test_hello(self):
        assertRegex(self, self.build('hello'),
                    re.compile(r'^\s*hello$', re.MULTILINE))

    def test_world(self):
        assertRegex(self, self.build('world'),
                    re.compile(r'^\s*world$', re.MULTILINE))

    def test_script(self):
        assertRegex(self, self.build('script'),
                    re.compile(r'^\s*hello, world!$', re.MULTILINE))
        self.assertExists(output_file('file'))

    def test_alias(self):
        output = self.build('hello-world')
        assertRegex(self, output, re.compile(r'^\s*hello$', re.MULTILINE))
        assertRegex(self, output, re.compile(r'^\s*world$', re.MULTILINE))


@skip_if_backend('msbuild')
class TestRunExecutable(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'run_executable', *args, **kwargs)

    def test_env_run(self):
        self.assertExists(output_file('file.txt'))

    def test_cxx(self):
        assertRegex(self, self.build('cxx'),
                    re.compile(r'^\s*hello from c\+\+!$', re.MULTILINE))

    def test_java(self):
        assertRegex(self, self.build('java'),
                    re.compile(r'^\s*hello from java!$', re.MULTILINE))

    def test_java_classlist(self):
        assertRegex(self, self.build('java-classlist'),
                    re.compile(r'^\s*hello from java!$', re.MULTILINE))

    def test_python(self):
        assertRegex(self, self.build('python'),
                    re.compile(r'^\s*hello from python!$', re.MULTILINE))
