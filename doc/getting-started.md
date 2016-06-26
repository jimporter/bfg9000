# Getting Started

## Supported platforms/languages

bfg9000 is designed to work on Linux, OS X, and Windows; other POSIX systems
should work as well, but they aren't explicitly supported (if you'd like to help
add support for your favorite platform, just file a pull request!). In addition,
bfg9000 supports building code written in the following languages:

* C
* C++
* Fortran (partial)
* Objective C/C++

## Installation

bfg9000 uses [setuptools](https://pythonhosted.org/setuptools/), so installation
is much the same as any other Python package:

```sh
$ pip install bfg9000
```

If you've downloaded bfg already, just run `pip install .` from the source
directory. (Equivalently, you can run `python setup.py install`.) From there,
you can start using bfg to build your software!

!!! note
    If you're using Ubuntu, you can also install bfg9000 from the following PPA:
    [ppa:jimporter/stable](https://launchpad.net/~jimporter/+archive/ubuntu/stable).

### Installing patchelf

On Linux, bfg9000 requires [patchelf](https://nixos.org/patchelf.html) in order
to modify [rpath](https://en.wikipedia.org/wiki/Rpath)s of executables and
shared libraries when installing. If you don't already have patchelf installed
(e.g. via your distro's package manager) and in your `PATH`, bfg9000 will
automatically install it via the
[patchelf-wrapper](https://pypi.python.org/pypi/patchelf-wrapper) package. If
you'd prefer not to install patchelf at all, you can set the `NO_PATCHELF`
environment variable to 1 before installing bfg9000:

```sh
$ NO_PATCHELF=1 pip install bfg9000
```

This will automatically download and install patchelf when installing the rest
of bfg9000. If you're installing into a
[virtualenv](https://virtualenv.readthedocs.org/en/latest/), patchelf
will go into `$VIRTUAL_ENV/bin`.

### Installing MSBuild support

Since many users don't need it, MSBuild support is an optional feature. To
install all the dependencies required for MSBuild, you can run the following:

```sh
$ pip install bfg9000[msbuild]
```
