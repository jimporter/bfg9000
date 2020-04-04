import os.path

from . import *


class TestCommand(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__(os.path.join(examples_dir, '08_commands'), *args,
                         **kwargs)

    def test_hello(self):
        self.assertRegex(self.build('hello'), r'(?m)^\s*hello$')

    def test_world(self):
        self.assertRegex(self.build('world'), r'(?m)^\s*world$')

    def test_script(self):
        self.assertRegex(self.build('script'), r'(?m)^\s*hello, world!$')
        self.assertExists(output_file('file'))

    def test_alias(self):
        output = self.build('hello-world')
        self.assertRegex(output, r'(?m)^\s*hello$')
        self.assertRegex(output, r'(?m)^\s*world$')


@skip_if_backend('msbuild')
class TestRunExecutable(IntegrationTest):
    def __init__(self, *args, **kwargs):
        super().__init__('run_executable', *args, **kwargs)

    def test_env_run(self):
        self.assertExists(output_file('file.txt'))

    def test_cxx(self):
        self.assertRegex(self.build('cxx'), r'(?m)^\s*hello from c\+\+!$')

    def test_java(self):
        self.assertRegex(self.build('java'), r'(?m)^\s*hello from java!$')

    def test_java_classlist(self):
        self.assertRegex(self.build('java-classlist'),
                         r'(?m)^\s*hello from java!$')

    def test_python(self):
        self.assertRegex(self.build('python'), r'(?m)^\s*hello from python!$')
