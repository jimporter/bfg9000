from .file_types import File, Node, sourcify
from .iterutils import iterate


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
