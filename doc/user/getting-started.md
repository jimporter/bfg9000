# Getting Started

## Supported platforms/languages

bfg9000 is designed to work on Linux, OS X, and Windows; other POSIX systems
should work as well, but they aren't explicitly supported (if you'd like to help
add support for your favorite platform, just file a pull request!). In addition,
bfg9000 supports building code written in the following languages:

* C
* C++
* Fortran (partial)
* Java
* Objective C/C++
* Scala

For more details on what you can do with bfg9000, see the
[features](features.md) page.

## Installation

bfg9000 uses [setuptools][setuptools], so installation is much the same as any
other Python package:

```sh
$ pip install bfg9000
```

If you've downloaded bfg already, just run `pip install .` from the source
directory. (Equivalently, you can run `python setup.py install`.) From there,
you can start using bfg to build your software!

!!! note
    If you're using Ubuntu, you can also install bfg9000 from the following PPA:
    [ppa:jimporter/stable][ppa].

Once you've installed bfg9000, you might also want to set up shell-completion
for it. If you have [shtab][shtab] installed, you can do this with
`bfg9000 generate-completion`, which will print the shell-completion code for
your shell to standard output. For more details on how to set this up, consult
shtab's [documentation][shtab-setup].

### External dependencies

In addition to a compiler for your chosen language, bfg9000 expects a few other
tools to be installed on your system:

* [`pkg-config`][pkg-config] (or an equivalent tool like [`pkgconf`][pfgconf]
* [`patchelf`][patchelf] on ELF-based systems (e.g. Linux)

### Installing MSBuild support

Since many users don't need it, MSBuild support is an optional feature. To
install all the dependencies required for MSBuild, you can run the following:

```sh
$ pip install bfg9000[msbuild]
```

## Editor integration

Since bfg9000 scripts are just Python scripts with some extra built-in
functions, it should be easy to get syntax highlighting for bfg9000 scripts in
your favorite editor. However, the extra builtins can cause spurious errors if
your editor expects to be able to look them up (e.g. via [LSP][lsp]). A more
robust alternative is to treat bfg9000 scripts as a different language. Emacs
users can do this by installing the [bfg9000-mode][bfg9000-mode] package.

If you want to treat bfg9000 scripts as bfg9000 when possible, but fall back to
Python otherwise, you can insert the following as the first line of your
scripts:

```python
# -*- mode: python; mode: bfg9000 -*-
```

Emacs (and other editors that understand Emacs' file-local variables) will use
the *last* `mode` available to the editor.

[setuptools]: https://pythonhosted.org/setuptools/
[ppa]: https://launchpad.net/~jimporter/+archive/ubuntu/stable
[shtab]: https://github.com/iterative/shtab
[shtab-setup]: https://github.com/iterative/shtab#cli-usage
[pkg-config]: https://www.freedesktop.org/wiki/Software/pkg-config/
[pkgconf]: http://pkgconf.org/
[patchelf]: https://nixos.org/patchelf.html
[virtualenv]: https://virtualenv.readthedocs.org/en/latest/
[lsp]: https://langserver.org/
[bfg9000-mode]: https://github.com/jimporter/bfg9000-mode
