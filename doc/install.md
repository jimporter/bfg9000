# Installation

bfg9000 uses [setuptools](https://pythonhosted.org/setuptools/), so installation
is much the same as any other Python package:

```sh
$ pip install bfg9000
```

If you've downloaded bfg, just run `pip install .` from the source directory.
(Equivalently, you can run `python setup.py install`.) From there, you can start
using bfg to build your software!

## Installing patchelf

On Linux, bfg9000 requires [patchelf](https://nixos.org/patchelf.html) in order
to modify [rpath](https://en.wikipedia.org/wiki/Rpath)s of executables and
shared libraries when installing. The best way to install this is to use your
distro's package manager, but if patchelf isn't listed, you can install patchelf
via pip:

```sh
$ pip install 'bfg9000[patchelf]'
```

This will automatically download and install patchelf when installing the rest
of bfg9000. If you're installing into a
[virtualenv](https://virtualenv.readthedocs.org/en/latest/), patchelf
will go into `$VIRTUAL_ENV/bin`.

## Installing MSBuild support

Since many users don't need it, MSBuild support is an optional feature. To
install all the dependencies required for MSBuild, you can run the following:

```sh
$ pip install bfg9000[msbuild]
```
