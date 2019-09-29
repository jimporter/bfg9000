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

    def test_write(self):
        proj = Project(FakeEnv(), 'project')
        self.sln[Phony('phony')] = proj

        out = StringIO()
        self.sln.write(out)
        assertRegex(
            self, out.getvalue(),
            r'(?m)^Project\("{[A-Z0-9-]+}"\) = "project", ' +
            r'"project.project\.proj", "{[A-Z0-9-]+}"$'
        )
