from six.moves import cStringIO as StringIO

from . import *

from bfg9000 import depfixer


class TestEmitDeps(TestCase):
    def test_empty_deps(self):
        instream = StringIO('foo:\n')
        outstream = StringIO()
        depfixer.emit_deps(instream, outstream)
        self.assertEqual(outstream.getvalue(), '')

    def test_single_dep(self):
        instream = StringIO('foo: bar\n')
        outstream = StringIO()
        depfixer.emit_deps(instream, outstream)
        self.assertEqual(outstream.getvalue(), 'bar:\n')

    def test_multiple_deps(self):
        instream = StringIO('foo: bar baz\n')
        outstream = StringIO()
        depfixer.emit_deps(instream, outstream)
        self.assertEqual(outstream.getvalue(), 'bar:\nbaz:\n')

    def test_multiline_deps(self):
        instream = StringIO('foo: bar\nbaz: quux\n')
        outstream = StringIO()
        depfixer.emit_deps(instream, outstream)
        self.assertEqual(outstream.getvalue(), 'bar:\nquux:\n')

    def test_multiple_targets(self):
        instream = StringIO('foo bar: baz quux\n')
        outstream = StringIO()
        depfixer.emit_deps(instream, outstream)
        self.assertEqual(outstream.getvalue(), 'baz:\nquux:\n')

    def test_windows_paths(self):
        instream = StringIO('c:\\foo c:\\bar: c:\\baz c:\\quux\n')
        outstream = StringIO()
        depfixer.emit_deps(instream, outstream)
        self.assertEqual(outstream.getvalue(), 'c:\\baz:\nc:\\quux:\n')

    def test_trailing_spaces(self):
        instream = StringIO('foo : bar \n')
        outstream = StringIO()
        depfixer.emit_deps(instream, outstream)
        self.assertEqual(outstream.getvalue(), 'bar:\n')

    def test_unexpected_newline(self):
        instream = StringIO('foo\n')
        outstream = StringIO()
        self.assertRaises(depfixer.UnexpectedTokenError, depfixer.emit_deps,
                          instream, outstream)

        instream = StringIO('foo \n')
        outstream = StringIO()
        self.assertRaises(depfixer.UnexpectedTokenError, depfixer.emit_deps,
                          instream, outstream)

    def test_unexpected_colon(self):
        instream = StringIO('foo: :\n')
        outstream = StringIO()
        self.assertRaises(depfixer.UnexpectedTokenError, depfixer.emit_deps,
                          instream, outstream)

        instream = StringIO('foo: bar :\n')
        outstream = StringIO()
        self.assertRaises(depfixer.UnexpectedTokenError, depfixer.emit_deps,
                          instream, outstream)

        instream = StringIO('foo: bar:\n')
        outstream = StringIO()
        self.assertRaises(depfixer.UnexpectedTokenError, depfixer.emit_deps,
                          instream, outstream)

    def test_unexpected_eof(self):
        instream = StringIO('foo: bar')
        outstream = StringIO()
        self.assertRaises(depfixer.ParseError, depfixer.emit_deps, instream,
                          outstream)
