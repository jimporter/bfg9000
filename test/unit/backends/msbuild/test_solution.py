from unittest import mock
from io import StringIO

from . import *

from bfg9000.backends.msbuild.solution import *
from bfg9000.backends.msbuild.syntax import Project
from bfg9000.file_types import File, Phony


class TestUuidMap(TestCase):
    _uuid_ex = r'[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}'

    def test_new(self):
        with mock.patch('builtins.open', side_effect=FileNotFoundError()):
            u = UuidMap('.bfg_uuid')
        foo = u['foo']
        self.assertRegex(str(foo), self._uuid_ex)
        self.assertEqual(u['foo'], foo)

    def test_existing(self):
        data = ('{"version": 1, "map": {' +
                '"foo": "00000000000000000000000000000001", ' +
                '"bar": "00000000000000000000000000000002"' +
                '}}')
        with mock.patch('builtins.open', mock.mock_open(read_data=data)):
            u = UuidMap('.bfg_uuid')

        self.assertEqual(str(u['foo']), '00000000-0000-0000-0000-000000000001')
        quux = u['quux']
        self.assertRegex(str(quux), self._uuid_ex)
        self.assertEqual(u['quux'], quux)

        with mock.patch('builtins.open', mock.mock_open()), \
             mock.patch('json.dump') as m:
            u.save()
            self.assertEqual(m.mock_calls[0][1][0], {
                'version': 1,
                'map': {'foo': '00000000000000000000000000000001',
                        'quux': quux.hex},
            })

        # Bad version
        data = '{"version": 2, "map": {}}'
        with mock.patch('builtins.open', mock.mock_open(read_data=data)):
            self.assertRaises(ValueError, UuidMap, '.bfg_uuid')


class TestSlnBuilder(TestCase):
    def assertElement(self, element, name, arg=None, value=None):
        self.assertIsInstance(element, SlnElement)
        self.assertEqual(element.name, name)
        self.assertEqual(element.arg, arg)
        self.assertEqual(element.value, value)

    def test_create_element(self):
        S = SlnBuilder()
        self.assertElement(S('Elt'), 'Elt')
        self.assertElement(S.Elt(), 'Elt')
        self.assertElement(S('Elt', 'arg', 'value'), 'Elt', 'arg', 'value')
        self.assertElement(S.Elt('arg', 'value'), 'Elt', 'arg', 'value')

    def test_children(self):
        foo = SlnElement('Foo')
        bar = SlnElement('Bar')

        e = SlnElement('Elt')
        e.append(foo)
        self.assertEqual(e.children, [foo])

        e = SlnElement('Elt')
        e.extend([foo, bar])
        self.assertEqual(e.children, [foo, bar])

        e = SlnElement('Elt')
        e(foo, bar)
        self.assertEqual(e.children, [foo, bar])

    def test_invalid(self):
        with self.assertRaises(TypeError):
            SlnElement('Elt', arg='arg')
        with self.assertRaises(TypeError):
            SlnElement('Elt', value='value')


class TestSolution(TestCase):
    def setUp(self):
        with mock.patch('builtins.open', side_effect=FileNotFoundError()):
            u = UuidMap('.bfg_uuid')
        self.sln = Solution(u)

    def test_add_project(self):
        proj = Project(FakeEnv(), 'project')
        self.sln[Phony('phony')] = proj

        self.assertTrue(Phony('phony') in self.sln)
        self.assertTrue(Phony('foobar') not in self.sln)
        self.assertTrue(File(Path('phony')) not in self.sln)
        self.assertIs(self.sln[Phony('phony')], proj)
        self.assertEqual(list(iter(self.sln)), [proj])

    def test_dependencies(self):
        class MockOutput:
            class MockCreator:
                def __init__(self, output):
                    self.public_output = output

            def __init__(self, output=None):
                self.creator = self.MockCreator(output) if output else None

        output = Phony('dep')
        proj = Project(FakeEnv(), 'project')
        self.sln[output] = proj
        self.assertEqual(
            self.sln.dependencies([ MockOutput(), MockOutput([output]) ]),
            [proj]
        )

        with self.assertRaises(RuntimeError):
            self.sln.dependencies([ MockOutput([Phony('wrong')]) ])

    def test_set_default(self):
        foo_proj = Project(FakeEnv(), 'foo_proj')
        self.sln[Phony('foo')] = foo_proj
        bar_proj = Project(FakeEnv(), 'bar_proj')
        self.sln[Phony('bar')] = bar_proj

        self.assertEqual(list(iter(self.sln)), [foo_proj, bar_proj])

        self.sln.set_default(Phony('bar'))
        self.assertEqual(list(iter(self.sln)), [bar_proj, foo_proj])

        self.sln.set_default(Phony('nonexist'))
        self.assertEqual(list(iter(self.sln)), [bar_proj, foo_proj])

    def test_write(self):
        class MockDependency:
            uuid_str = '{00000000-0000-0000-0000-000000000001}'

        foo_proj = Project(FakeEnv(), 'foo_proj')
        self.sln[Phony('foo')] = foo_proj
        bar_proj = Project(FakeEnv(), 'bar_proj', dependencies=[foo_proj])
        self.sln[Phony('bar')] = bar_proj

        out = StringIO()
        self.sln.write(out)
        guid_ex = '{[A-Z0-9-]+}'
        self.assertRegex(out.getvalue(), (
            r'(?m)^Project\("{0}"\) = "{1}", "{1}.{1}\.proj", "{0}"\n'
            r'EndProject\n'
            r'Project\("{0}"\) = "{2}", "{2}.{2}\.proj", "{0}"\n'
            r'\tProjectSection\(ProjectDependencies\) = postProject\n'
            r'\t\t{0} = {0}\n'
            r'\tEndProjectSection\n'
            r'EndProject$'
        ).format(guid_ex, 'foo_proj', 'bar_proj'))

    def test_write_set_default(self):
        class MockDependency:
            uuid_str = '{00000000-0000-0000-0000-000000000001}'

        foo_proj = Project(FakeEnv(), 'foo_proj')
        self.sln[Phony('foo')] = foo_proj
        bar_proj = Project(FakeEnv(), 'bar_proj', dependencies=[foo_proj])
        self.sln[Phony('bar')] = bar_proj
        self.sln.set_default(Phony('bar'))

        out = StringIO()
        self.sln.write(out)
        guid_ex = '{[A-Z0-9-]+}'
        self.assertRegex(out.getvalue(), (
            r'(?m)^Project\("{0}"\) = "{1}", "{1}.{1}\.proj", "{0}"\n'
            r'\tProjectSection\(ProjectDependencies\) = postProject\n'
            r'\t\t{0} = {0}\n'
            r'\tEndProjectSection\n'
            r'EndProject\n'
            r'Project\("{0}"\) = "{2}", "{2}.{2}\.proj", "{0}"\n'
            r'EndProject$'
        ).format(guid_ex, 'bar_proj', 'foo_proj'))
