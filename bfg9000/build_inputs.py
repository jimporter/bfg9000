from six import string_types

from . import path
from .iterutils import iterate
from .safe_str import safe_str


class Node(object):
    def __init__(self):
        self.creator = None

    @property
    def all(self):
        return [self]

    def _safe_str(self):
        return safe_str(self.path)

    def __repr__(self):
        return '<{type} {name}>'.format(
            type=type(self).__name__, name=repr(self.path)
        )


def objectify(thing, valid_type, creator, *args, **kwargs):
    if isinstance(thing, valid_type):
        return thing
    elif not isinstance(thing, string_types):
        raise TypeError('expected a {} or a string'.format(valid_type))
    else:
        if creator is None:
            creator = valid_type
        # XXX: Come up with a way to provide args to prepend?
        return creator(thing, *args, **kwargs)


def sourcify(thing, valid_type, make_type=None, **kwargs):
    return objectify(thing, valid_type, make_type, root=path.Root.srcdir,
                     **kwargs)


class File(Node):
    install_kind = None
    install_root = None

    def __init__(self, name, root):
        Node.__init__(self)
        self.path = path.Path(name, root)
        self.post_install = None


class Directory(File):
    pass


class Phony(Node):
    def __init__(self, name):
        Node.__init__(self)
        self.path = name


class Edge(object):
    def __init__(self, build, target, extra_deps=None):
        for t in target.all:
            t.creator = self
        self.target = target

        self.extra_deps = [sourcify(i, Node, File)
                           for i in iterate(extra_deps)]
        build.add_edge(self)


class InstallInputs(object):
    def __init__(self):
        self.files = []
        self.directories = []

    def __nonzero__(self):
        return bool(self.files or self.directories)


class TestInputs(object):
    def __init__(self):
        self.tests = []
        self.targets = []
        self.extra_deps = []

    def __nonzero__(self):
        return bool(self.tests)


class BuildInputs(object):
    def __init__(self):
        self.edges = []
        self.default_targets = []
        self.fallback_default = None
        self.install_targets = InstallInputs()
        self.tests = TestInputs()
        self.global_options = {}
        self.global_link_options = []
        self.find_dirs = set()

    def add_edge(self, edge):
        self.edges.append(edge)

    def get_default_targets(self):
        if self.default_targets:
            return self.default_targets
        elif self.fallback_default:
            return [self.fallback_default]
        else:
            return []
