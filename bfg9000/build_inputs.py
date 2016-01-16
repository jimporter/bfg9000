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


class InstallTargets(object):
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


class DefaultTargets(object):
    def __init__(self):
        self.default_targets = []
        self.fallback_defaults = []

    def add(self, target, explicit=False):
        targets = self.default_targets if explicit else self.fallback_defaults
        targets.append(target)

    def remove(self, target):
        for i, fallback in enumerate(self.fallback_defaults):
            if target is fallback:
                self.fallback_defaults.pop(i)

    @property
    def targets(self):
        return self.default_targets or self.fallback_defaults


class BuildInputs(object):
    def __init__(self):
        self.edges = []
        self.defaults = DefaultTargets()
        self.install_targets = InstallTargets()
        self.tests = TestInputs()
        self.global_options = {}
        self.global_link_options = []
        self.find_dirs = set()

    def add_edge(self, edge):
        self.edges.append(edge)
