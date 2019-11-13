from .common import BuiltinTest

from bfg9000.builtins import project  # noqa


class TestProject(BuiltinTest):
    def test_default(self):
        self.assertEqual(self.build['project'].name, 'srcdir')
        self.assertEqual(self.build['project'].version, None)
        self.assertEqual(self.build['project']['intermediate_dirs'], True)
        self.assertEqual(self.build['project']['lang'], 'c')

    def test_name(self):
        self.builtin_dict['project']('project-name')
        self.assertEqual(self.build['project'].name, 'project-name')
        self.assertEqual(self.build['project'].version, None)
        self.assertEqual(self.build['project']['intermediate_dirs'], True)
        self.assertEqual(self.build['project']['lang'], 'c')

    def test_version(self):
        self.builtin_dict['project'](version='1.0')
        self.assertEqual(self.build['project'].name, 'srcdir')
        self.assertEqual(self.build['project'].version, '1.0')
        self.assertEqual(self.build['project']['lang'], 'c')
        self.assertEqual(self.build['project']['intermediate_dirs'], True)

    def test_options(self):
        self.builtin_dict['project'](intermediate_dirs=False)
        self.assertEqual(self.build['project'].name, 'srcdir')
        self.assertEqual(self.build['project'].version, None)
        self.assertEqual(self.build['project']['intermediate_dirs'], False)
        self.assertEqual(self.build['project']['lang'], 'c')

    def test_multi(self):
        self.builtin_dict['project']('project-name', '1.0',
                                     intermediate_dirs=False)
        self.assertEqual(self.build['project'].name, 'project-name')
        self.assertEqual(self.build['project'].version, '1.0')
        self.assertEqual(self.build['project']['intermediate_dirs'], False)
        self.assertEqual(self.build['project']['lang'], 'c')

    def test_invalid_option(self):
        with self.assertRaises(KeyError):
            self.builtin_dict['project'](unknown=True)
