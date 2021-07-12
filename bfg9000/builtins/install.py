import warnings
from collections import OrderedDict

from . import builtin
from .. import path
from .. import shell
from ..backends.make import writer as make
from ..backends.ninja import writer as ninja
from ..build_inputs import build_input
from ..file_types import BaseFile, Directory
from ..iterutils import flatten, iterate, map_iterable, unlistify


@build_input('install')
class InstallOutputs:
    def __init__(self, build_inputs, env):
        self.explicit = []
        self.host = OrderedDict()
        self.target = OrderedDict()
        self.env = env

    def add(self, item, directory=None):
        if item not in self.explicit:
            self.explicit.append(item)
        return self._add_implicit(item, directory)

    def _add_implicit(self, item, directory):
        host = installify(item, directory=directory)
        target = installify(item, directory=directory, cross=self.env)
        assert len(item.all) == len(host.all) == len(target.all)
        for src, h, t in zip(item.all, host.all, target.all):
            if src in self.host:
                if self.host[src].path != h.path:
                    raise ValueError(('{!r} already installed to a ' +
                                      'different location').format(src.path))
            else:
                self.host[src] = h
                self.target[src] = t

            for dep in src.install_deps:
                self._add_implicit(dep, directory)

        return target

    def __bool__(self):
        return bool(self.explicit)

    def __iter__(self):
        return iter(self.host)


def installify(file, *, directory=None, cross=None):
    def pathfn(f):
        if f is not file and f.private:
            # Private subfiles won't (and in some cases can't) be installed.
            return f.path
        if f.path.root not in (path.Root.srcdir, path.Root.builddir):
            raise ValueError('external files are not installable')

        # Get the install root.
        if isinstance(directory, path.Path):
            install_root = directory
            if not isinstance(install_root.root, path.InstallRoot):
                raise ValueError('not an install directory')
        elif f.install_root is None:
            raise TypeError(('{!r} is not installable; specify an absolute ' +
                             'install directory?').format(type(f).__name__))
        elif directory:
            install_root = path.Path(directory, f.install_root)
        else:
            install_root = f.install_root

        cls = cross.target_platform.Path if cross else type(f.path)
        return cls(f.install_suffix, install_root, destdir=not cross)

    if not isinstance(file, BaseFile):
        raise TypeError('expected a file or directory')
    return file.clone(pathfn, recursive=True)


def can_install(env):
    return all(i is not None for i in env.install_dirs.values())


@builtin.function()
def install(context, *args, directory=None):
    if len(args) == 0:
        return

    can_inst = can_install(context.env)
    if not can_inst:
        warnings.warn('unset installation directories; installation of this ' +
                      'build disabled')

    context['default'](*args)
    return unlistify(tuple(map_iterable(
        lambda i: context.build['install'].add(i, directory), i
    ) for i in args))


def _doppel_cmd(env, buildfile):
    doppel = env.tool('doppel')

    def wrapper(kind):
        cmd_var = buildfile.cmd_var(doppel)
        cmd = [cmd_var] + doppel.kind_args(kind)

        basename = cmd_var.name
        if basename.isupper():
            kind = kind.upper()
        name = '{name}_{kind}'.format(name=basename, kind=kind)

        cmd = buildfile.variable(name, cmd, buildfile.Section.command, True)
        return lambda *args, **kwargs: doppel(*args, cmd=cmd, **kwargs)
    return wrapper


def _install_files(install_outputs, buildfile, env):
    doppel = _doppel_cmd(env, buildfile)

    def install_line(src, dst):
        cmd = doppel(src.install_kind)
        if isinstance(src, Directory):
            if src.files is not None:
                src_paths = [i.path.relpath(src.path) for i in src.files]
                return cmd('into', src_paths, dst.path, directory=src.path)

            warnings.warn(
                ('installed directory {!r} has no matching files; did you ' +
                 'forget to set `include`?').format(src.path)
            )

        return cmd('onto', src.path, dst.path)

    def post_install(i):
        return i.post_install(install_outputs) if i.post_install else None

    return ([install_line(*i) for i in install_outputs.host.items()] +
            list(filter( None, (post_install(i) for i in install_outputs) )))


def _install_mopack(env):
    if env.mopack:
        return [env.tool('mopack')('deploy', directory=path.Path('.'))]
    return []


def _uninstall_files(install_outputs, env):
    def uninstall_line(src, dst):
        if isinstance(src, Directory):
            return [dst.path.append(i.path.relpath(src.path)) for i in
                    iterate(src.files)]
        return [dst.path]

    if install_outputs:
        return [env.tool('rm')(flatten(
            uninstall_line(*i) for i in install_outputs.host.items()
        ))]
    return []


def _add_install_paths(buildfile, env):
    for i in path.InstallRoot:
        buildfile.variable(buildfile.path_vars[i], env.install_dirs[i],
                           buildfile.Section.path)
    if path.DestDir.destdir in buildfile.path_vars:
        buildfile.variable(buildfile.path_vars[path.DestDir.destdir],
                           env.variables.get('DESTDIR', ''),
                           buildfile.Section.path)


@make.post_rule
def make_install_rule(build_inputs, buildfile, env):
    if not can_install(env):
        return

    install_outputs = build_inputs['install']
    install_files = _install_files(install_outputs, buildfile, env)
    uninstall_files = _uninstall_files(install_outputs, env)

    if install_files or uninstall_files:
        _add_install_paths(buildfile, env)

    install_commands = install_files + _install_mopack(env)

    if install_commands:
        buildfile.rule(
            target='install',
            deps='all',
            recipe=install_commands,
            phony=True
        )
    if uninstall_files:
        buildfile.rule(
            target='uninstall',
            recipe=uninstall_files,
            phony=True
        )


@ninja.post_rule
def ninja_install_rule(build_inputs, buildfile, env):
    if not can_install(env):
        return

    install_outputs = build_inputs['install']
    install_files = _install_files(install_outputs, buildfile, env)
    uninstall_files = _uninstall_files(install_outputs, env)

    if install_files or uninstall_files:
        _add_install_paths(buildfile, env)

    install_commands = install_files + _install_mopack(env)

    if install_commands:
        ninja.command_build(
            buildfile, env,
            output='install',
            inputs=['all'],
            command=shell.join_lines(install_commands),
            console=True,
            phony=True
        )
    if uninstall_files:
        ninja.command_build(
            buildfile, env,
            output='uninstall',
            command=shell.join_lines(uninstall_files),
            phony=True
        )
