from .common import BuiltinTest

from bfg9000.builtins import compile, default, link, packages, project  # noqa


class TestDefaultOutputs(BuiltinTest):
    def setUp(self):
        BuiltinTest.setUp(self)
        self.default = default.DefaultOutputs(self.build, self.env)

    def test_add_remove(self):
        obj = self.builtin_dict['object_file'](file='src.cpp')
        self.default.add(obj)
        self.assertEqual(self.default.outputs, [obj])

        self.default.remove(obj)
        self.assertEqual(self.default.outputs, [])

    def test_add_remove_explicit(self):
        obj1 = self.builtin_dict['object_file'](file='src1.cpp')
        obj2 = self.builtin_dict['object_file'](file='src2.cpp')
        self.default.add(obj1)
        self.default.add(obj2, explicit=True)
        self.assertEqual(self.default.outputs, [obj2])

        self.default.remove(obj1, explicit=True)
        self.assertEqual(self.default.outputs, [obj2])
        self.default.remove(obj2, explicit=True)
        self.assertEqual(self.default.outputs, [obj1])

    def test_add_no_creator(self):
        obj = self.builtin_dict['object_file']('obj.o')
        self.default.add(obj)
        self.assertEqual(self.default.outputs, [])

        self.default.add(obj, explicit=True)
        self.assertEqual(self.default.outputs, [])


class TestDefault(BuiltinTest):
    def test_single_result(self):
        obj = self.builtin_dict['object_file'](file='src.cpp')
        self.assertEqual(self.builtin_dict['default'](obj), obj)
        self.assertEqual(self.build['defaults'].outputs, [obj])

    def test_multiple_results(self):
        obj1 = self.builtin_dict['object_file'](file='src1.cpp')
        obj2 = self.builtin_dict['object_file'](file='src2.cpp')
        self.assertEqual(self.builtin_dict['default'](obj1, obj2),
                         (obj1, obj2))
        self.assertEqual(self.build['defaults'].outputs, [obj1, obj2])

    def test_nested_results(self):
        obj1 = self.builtin_dict['object_file'](file='src1.cpp')
        obj2 = self.builtin_dict['object_file'](file='src2.cpp')
        self.assertEqual(self.builtin_dict['default'](obj1, [obj2], None),
                         (obj1, [obj2], None))
        self.assertEqual(self.build['defaults'].outputs, [obj1, obj2])
