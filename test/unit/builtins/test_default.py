from .common import BuiltinTestCase

from bfg9000.builtins import (compile, default, link, packages,  # noqa: F401
                              project)


class TestDefaultOutputs(BuiltinTestCase):
    def setUp(self):
        super().setUp()
        self.default = default.DefaultOutputs()

    def test_add_remove(self):
        obj = self.context['object_file'](file='src.cpp')
        self.default.add(obj)
        self.assertEqual(self.default.outputs, [obj])

        self.default.remove(obj)
        self.assertEqual(self.default.outputs, [])

    def test_add_remove_explicit(self):
        obj1 = self.context['object_file'](file='src1.cpp')
        obj2 = self.context['object_file'](file='src2.cpp')
        self.default.add(obj1)
        self.default.add(obj2, explicit=True)
        self.assertEqual(self.default.outputs, [obj2])

        self.default.remove(obj1, explicit=True)
        self.assertEqual(self.default.outputs, [obj2])
        self.default.remove(obj2, explicit=True)
        self.assertEqual(self.default.outputs, [obj1])

    def test_add_no_creator(self):
        obj = self.context['object_file']('obj.o')
        self.default.add(obj)
        self.assertEqual(self.default.outputs, [])

        self.default.add(obj, explicit=True)
        self.assertEqual(self.default.outputs, [])


class TestDefault(BuiltinTestCase):
    def test_single_result(self):
        obj = self.context['object_file'](file='src.cpp')
        self.assertEqual(self.context['default'](obj), obj)
        self.assertEqual(self.build['defaults'].outputs, [obj])

    def test_multiple_results(self):
        obj1 = self.context['object_file'](file='src1.cpp')
        obj2 = self.context['object_file'](file='src2.cpp')
        self.assertEqual(self.context['default'](obj1, obj2),
                         (obj1, obj2))
        self.assertEqual(self.build['defaults'].outputs, [obj1, obj2])

    def test_nested_results(self):
        obj1 = self.context['object_file'](file='src1.cpp')
        obj2 = self.context['object_file'](file='src2.cpp')
        self.assertEqual(self.context['default'](obj1, [obj2], None),
                         (obj1, [obj2], None))
        self.assertEqual(self.build['defaults'].outputs, [obj1, obj2])
