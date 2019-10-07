import os.path

from . import *


class TestCommand(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, os.path.join(examples_dir, '08_commands'), *args, **kwargs
        )

    def test_hello(self):
        assertRegex(self, self.build('hello'), r'(?m)^\s*hello$')

    def test_world(self):
        assertRegex(self, self.build('world'), r'(?m)^\s*world$')

    def test_script(self):
        assertRegex(self, self.build('script'), r'(?m)^\s*hello, world!$')
        self.assertExists(output_file('file'))

    def test_alias(self):
        output = self.build('hello-world')
        assertRegex(self, output, r'(?m)^\s*hello$')
        assertRegex(self, output, r'(?m)^\s*world$')


@skip_if_backend('msbuild')
class TestRunExecutable(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'run_executable', *args, **kwargs)

    def test_env_run(self):
        self.assertExists(output_file('file.txt'))

    def test_cxx(self):
        assertRegex(self, self.build('cxx'), r'(?m)^\s*hello from c\+\+!$')

    def test_java(self):
        assertRegex(self, self.build('java'), r'(?m)^\s*hello from java!$')

    def test_java_classlist(self):
        assertRegex(self, self.build('java-classlist'),
                    r'(?m)^\s*hello from java!$')

    def test_python(self):
        assertRegex(self, self.build('python'), r'(?m)^\s*hello from python!$')
