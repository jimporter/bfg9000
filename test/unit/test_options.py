import unittest

from bfg9000.options import *


class TestOptionList(unittest.TestCase):
    def test_empty(self):
        opts = option_list()
        self.assertEqual(list(opts), [])

    def test_filled(self):
        opts = option_list(pthread())
        self.assertEqual(list(opts), [pthread()])

        opts = option_list([pthread()])
        self.assertEqual(list(opts), [pthread()])

        opts = option_list(pthread(), [pic()])
        self.assertEqual(list(opts), [pthread(), pic()])

    def test_append(self):
        opts = option_list()
        opts.append(pthread())
        opts.append(pthread())
        self.assertEqual(list(opts), [pthread()])

        opts = option_list()
        opts.append('-v')
        opts.append('-v')
        self.assertEqual(list(opts), ['-v', '-v'])

    def test_extend(self):
        opts = option_list()
        opts.extend([pthread(), pic()])
        self.assertEqual(list(opts), [pthread(), pic()])

        opts = option_list(pthread())
        opts.extend([pthread(), pic()])
        self.assertEqual(list(opts), [pthread(), pic()])

    def test_collect(self):
        opts = option_list()
        opts.collect(pthread())
        self.assertEqual(list(opts), [pthread()])

        opts = option_list()
        opts.collect([pthread()])
        self.assertEqual(list(opts), [pthread()])

        opts = option_list()
        opts.collect(pthread(), [pic()])
        self.assertEqual(list(opts), [pthread(), pic()])

    def test_copy(self):
        opts = option_list(pthread(), [pic()])
        opts2 = opts.copy()
        self.assertTrue(opts is not opts2)
        self.assertEqual(opts, opts2)

    def test_iter(self):
        opts = option_list(pthread(), pic())
        self.assertEqual(list(iter(opts)), [pthread(), pic()])

    def test_len(self):
        opts = option_list()
        self.assertEqual(len(opts), 0)

        opts = option_list(pthread())
        self.assertEqual(len(opts), 1)

        opts = option_list(pthread(), pic())
        self.assertEqual(len(opts), 2)

    def test_eq(self):
        opts1 = option_list(pthread())
        opts2 = option_list(pthread())
        opts3 = option_list(pic())

        self.assertTrue(opts1 == opts2)
        self.assertFalse(opts1 != opts2)
        self.assertFalse(opts1 == opts3)
        self.assertTrue(opts1 != opts3)

    def test_add(self):
        opts1 = option_list(pthread())
        opts2 = option_list(pthread())
        opts3 = option_list(pic())

        self.assertEqual(opts1 + opts2 + opts3, option_list(pthread(), pic()))
        with self.assertRaises(TypeError):
            opts1 + [pic()]

    def test_iadd(self):
        opts = option_list(pthread())
        opts += option_list(pthread())
        opts += option_list(pic())

        self.assertEqual(opts, option_list(pthread(), pic()))
        with self.assertRaises(TypeError):
            opts += [pic()]


class TestOption(unittest.TestCase):
    def test_create(self):
        my_option = option('my_option', ['value'])

        o = my_option('foo')
        self.assertEqual(type(o), my_option)
        self.assertEqual(o.value, 'foo')

        o = my_option(value='foo')
        self.assertEqual(type(o), my_option)
        self.assertEqual(o.value, 'foo')

    def test_multiple_values(self):
        my_option = option('my_option', ['name', 'value'])

        o = my_option('foo', 'bar')
        self.assertEqual(type(o), my_option)
        self.assertEqual(o.name, 'foo')
        self.assertEqual(o.value, 'bar')

        o = my_option(name='foo', value='bar')
        self.assertEqual(type(o), my_option)
        self.assertEqual(o.name, 'foo')
        self.assertEqual(o.value, 'bar')

    def test_typed(self):
        my_option = option('my_option', [('value', str)])
        self.assertEqual(my_option('foo').value, 'foo')
        self.assertRaises(TypeError, my_option, 1)

        my_option = option('my_option', [('value', (str, int))])
        self.assertEqual(my_option('foo').value, 'foo')
        self.assertEqual(my_option(1).value, 1)
        self.assertRaises(TypeError, my_option, 1.2)

    def test_matches(self):
        my_option = option('my_option', ['value'])
        o1 = my_option('foo')
        o2 = my_option('foo')
        o3 = my_option('bar')

        self.assertTrue(o1.matches(o2))
        self.assertFalse(o1.matches(o3))

    def test_eq(self):
        my_option = option('my_option', ['value'])
        o1 = my_option('foo')
        o2 = my_option('foo')
        o3 = my_option('bar')

        self.assertTrue(o1 == o2)
        self.assertFalse(o1 != o2)
        self.assertFalse(o1 == o3)
        self.assertTrue(o1 != o3)


class TestDefine(unittest.TestCase):
    def test_name_only(self):
        opt = define('NAME')
        self.assertEqual(type(opt), define)
        self.assertEqual(opt.name, 'NAME')
        self.assertEqual(opt.value, None)

    def test_name_and_value(self):
        opt = define('NAME', 'value')
        self.assertEqual(type(opt), define)
        self.assertEqual(opt.name, 'NAME')
        self.assertEqual(opt.value, 'value')

    def test_invalid_type(self):
        self.assertRaises(TypeError, define, 1)
        self.assertRaises(TypeError, define, 'NAME', 1)
