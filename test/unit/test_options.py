from . import *

from bfg9000 import options


class TestOptionList(TestCase):
    def test_empty(self):
        opts = options.option_list()
        self.assertEqual(list(opts), [])

    def test_filled(self):
        opts = options.option_list(options.pthread())
        self.assertEqual(list(opts), [options.pthread()])

        opts = options.option_list([options.pthread()])
        self.assertEqual(list(opts), [options.pthread()])

        opts = options.option_list(options.pthread(), [options.pic()])
        self.assertEqual(list(opts), [options.pthread(), options.pic()])

    def test_append(self):
        opts = options.option_list()
        opts.append(options.pthread())
        opts.append(options.pthread())
        self.assertEqual(list(opts), [options.pthread()])

        opts = options.option_list()
        opts.append('-v')
        opts.append('-v')
        self.assertEqual(list(opts), ['-v', '-v'])

    def test_extend(self):
        opts = options.option_list()
        opts.extend([options.pthread(), options.pic()])
        self.assertEqual(list(opts), [options.pthread(), options.pic()])

        opts = options.option_list(options.pthread())
        opts.extend([options.pthread(), options.pic()])
        self.assertEqual(list(opts), [options.pthread(), options.pic()])

    def test_collect(self):
        opts = options.option_list()
        opts.collect(options.pthread())
        self.assertEqual(list(opts), [options.pthread()])

        opts = options.option_list()
        opts.collect([options.pthread()])
        self.assertEqual(list(opts), [options.pthread()])

        opts = options.option_list()
        opts.collect(options.pthread(), [options.pic()])
        self.assertEqual(list(opts), [options.pthread(), options.pic()])

    def test_copy(self):
        opts = options.option_list(options.pthread(), [options.pic()])
        opts2 = opts.copy()
        self.assertTrue(opts is not opts2)
        self.assertEqual(opts, opts2)

    def test_filter(self):
        opts = options.option_list(options.pthread(), options.pic())
        opts2 = opts.filter(options.pic)
        self.assertEqual(opts2, options.option_list(options.pic()))

    def test_iter(self):
        opts = options.option_list(options.pthread(), options.pic())
        self.assertEqual(list(iter(opts)), [options.pthread(), options.pic()])

    def test_len(self):
        opts = options.option_list()
        self.assertEqual(len(opts), 0)

        opts = options.option_list(options.pthread())
        self.assertEqual(len(opts), 1)

        opts = options.option_list(options.pthread(), options.pic())
        self.assertEqual(len(opts), 2)

    def test_bool(self):
        opts = options.option_list()
        self.assertFalse(opts)

        opts = options.option_list(options.pthread())
        self.assertTrue(opts)

        opts = options.option_list(options.pthread(), options.pic())
        self.assertEqual(len(opts), 2)

    def test_index(self):
        opts = options.option_list(options.pthread(), options.pic())
        self.assertEqual(opts[0], options.pthread())
        self.assertEqual(opts[0:1], options.option_list(options.pthread()))

        opts[0] = '-v'
        self.assertEqual(opts, options.option_list('-v', options.pic()))
        opts[0:] = [options.define('name')]
        self.assertEqual(opts, options.option_list(options.define('name')))

    def test_equality(self):
        opts1 = options.option_list(options.pthread())
        opts2 = options.option_list(options.pthread())
        opts3 = options.option_list(options.pic())

        self.assertTrue(opts1 == opts2)
        self.assertFalse(opts1 != opts2)
        self.assertFalse(opts1 == opts3)
        self.assertTrue(opts1 != opts3)

    def test_add(self):
        opts1 = options.option_list(options.pthread())
        opts2 = options.option_list(options.pthread())
        opts3 = options.option_list(options.pic())

        self.assertEqual(opts1 + opts2 + opts3,
                         options.option_list(options.pthread(), options.pic()))
        with self.assertRaises(TypeError):
            opts1 + [options.pic()]

    def test_iadd(self):
        opts = options.option_list(options.pthread())
        opts += options.option_list(options.pthread())
        opts += options.option_list(options.pic())

        self.assertEqual(opts, options.option_list(options.pthread(),
                                                   options.pic()))
        with self.assertRaises(TypeError):
            opts += [options.pic()]


class TestOption(TestCase):
    def test_create(self):
        my_option = options.option('my_option', value=object)

        o = my_option('foo')
        self.assertEqual(type(o), my_option)
        self.assertEqual(o.value, 'foo')

        o = my_option(value='foo')
        self.assertEqual(type(o), my_option)
        self.assertEqual(o.value, 'foo')

    def test_multiple_values(self):
        my_option = options.option('my_option', name=object, value=object)

        o = my_option('foo', 'bar')
        self.assertEqual(type(o), my_option)
        self.assertEqual(o.name, 'foo')
        self.assertEqual(o.value, 'bar')

        o = my_option(name='foo', value='bar')
        self.assertEqual(type(o), my_option)
        self.assertEqual(o.name, 'foo')
        self.assertEqual(o.value, 'bar')

    def test_typed(self):
        my_option = options.option('my_option', value=str)
        self.assertEqual(my_option('foo').value, 'foo')
        self.assertRaises(TypeError, my_option, 1)

        my_option = options.option('my_option', value=(str, int))
        self.assertEqual(my_option('foo').value, 'foo')
        self.assertEqual(my_option(1).value, 1)
        self.assertRaises(TypeError, my_option, 1.2)

    def test_enum(self):
        Value = options.OptionEnum('Value', ['foo', 'bar'])
        my_option = options.option('my_option', value=Value)

        self.assertEqual(my_option(Value.foo).value, Value.foo)
        self.assertEqual(my_option('foo').value, Value.foo)
        self.assertRaises(TypeError, my_option, 1)
        self.assertRaises(ValueError, my_option, 'unknown')

    def test_variadic(self):
        my_option = options.variadic_option('my_option')

        o = my_option()
        self.assertEqual(type(o), my_option)
        self.assertEqual(o.value, [])

        o = my_option('foo')
        self.assertEqual(type(o), my_option)
        self.assertEqual(o.value, ['foo'])

        o = my_option('foo', 'bar')
        self.assertEqual(type(o), my_option)
        self.assertEqual(o.value, ['foo', 'bar'])

    def test_variadic_type(self):
        my_option = options.variadic_option('my_option', int)

        self.assertEqual(my_option().value, [])
        self.assertEqual(my_option(1).value, [1])
        self.assertEqual(my_option(1, 2).value, [1, 2])

        self.assertRaises(TypeError, my_option, 'foo')

    def test_matches(self):
        my_option = options.option('my_option', value=object)
        o1 = my_option('foo')
        o2 = my_option('foo')
        o3 = my_option('bar')

        self.assertTrue(o1.matches(o2))
        self.assertFalse(o1.matches(o3))

    def test_equality(self):
        my_option = options.option('my_option', value=object)
        o1 = my_option('foo')
        o2 = my_option('foo')
        o3 = my_option('bar')

        self.assertTrue(o1 == o2)
        self.assertFalse(o1 != o2)
        self.assertFalse(o1 == o3)
        self.assertTrue(o1 != o3)


class TestDefine(TestCase):
    def test_name_only(self):
        opt = options.define('NAME')
        self.assertEqual(type(opt), options.define)
        self.assertEqual(opt.name, 'NAME')
        self.assertEqual(opt.value, None)

    def test_name_and_value(self):
        opt = options.define('NAME', 'value')
        self.assertEqual(type(opt), options.define)
        self.assertEqual(opt.name, 'NAME')
        self.assertEqual(opt.value, 'value')

    def test_invalid_type(self):
        self.assertRaises(TypeError, options.define, 1)
        self.assertRaises(TypeError, options.define, 'NAME', 1)
