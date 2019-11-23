import mock
from six.moves import cStringIO as StringIO

from . import *

from bfg9000.backends.msbuild.solution import *
from bfg9000.backends.msbuild.syntax import Project
from bfg9000.file_types import File, Phony


def bad_open(s):
    raise IOError()


class TestUuidMap(TestCase):
    _uuid_ex = r'[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}'

    def test_new(self):
        with mock.patch(mock_open_name, bad_open):
            u = UuidMap('.bfg_uuid')
        foo = u['foo']
        assertRegex(self, str(foo), self._uuid_ex)
        self.assertEqual(u['foo'], foo)

    def test_existing(self):
        data = ('{"version": 1, "map": {' +
                  '"foo": "00000000000000000000000000000001", ' +
                  '"bar": "00000000000000000000000000000002"' +
                '}}')  # noqa
        with mock.patch(mock_open_name, mock_open(read_data=data)):
            u = UuidMap('.bfg_uuid')

        self.assertEqual(str(u['foo']), '00000000-0000-0000-0000-000000000001')
        quux = u['quux']
        assertRegex(self, str(quux), self._uuid_ex)
        self.assertEqual(u['quux'], quux)

        with mock.patch(mock_open_name, mock_open()), \
             mock.patch('json.dump') as m:  # noqa
            u.save()
            self.assertEqual(m.mock_calls[0][1][0], {
                'version': 1,
                'map': {u'foo': '00000000000000000000000000000001',
                        'quux': quux.hex},
            })

        # Bad version
        data = '{"version": 2, "map": {}}'
        with mock.patch(mock_open_name, mock_open(read_data=data)):
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
        with mock.patch(mock_open_name, bad_open):
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
        class MockOutput(object):
            class MockCreator(object):
                def __init__(self, output):
                    self.output = output

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

    def test_write(self):
        class MockDependency(object):
            uuid_str = '{00000000-0000-0000-0000-000000000001}'

        foo_proj = Project(FakeEnv(), 'foo_proj')
        self.sln[Phony('foo')] = foo_proj
        bar_proj = Project(FakeEnv(), 'bar_proj', dependencies=[foo_proj])
        self.sln[Phony('bar')] = bar_proj

        out = StringIO()
        self.sln.write(out)
        guid_ex = '{[A-Z0-9-]+}'
        assertRegex(self, out.getvalue(), (
            r'(?m)^Project\("{0}"\) = "{1}", "{1}.{1}\.proj", "{0}"\n'
            r'EndProject$'
        ).format(guid_ex, 'foo_proj'))
        assertRegex(self, out.getvalue(), (
            r'(?m)^Project\("{0}"\) = "{1}", "{1}.{1}\.proj", "{0}"\n'
            r'\tProjectSection\(ProjectDependencies\) = postProject\n'
            r'\t\t{0} = {0}\n'
            r'\tEndProjectSection\n'
            r'EndProject$'
        ).format(guid_ex, 'bar_proj'))
