# Installation

bfg9000 uses [setuptools](http://pythonhosted.org/setuptools/), so installation
is much the same as any other Python package. After you've downloaded bfg, just
run this from the source directory:

```sh
$ pip install .
```

(Equivalently, you can run `python setup.py install`.) From there, you can start
using bfg to build your software!

## Installing patchelf

On Linux, bfg9000 requires [patchelf](https://nixos.org/patchelf.html) in order
to modify [rpath](https://en.wikipedia.org/wiki/Rpath)s of executables and
shared libraries when installing. The setup script will automatically download
and install patchelf when installing the rest of bfg9000. If you're installing
bfg into a [virtualenv](http://virtualenv.readthedocs.org/en/latest/), patchelf
will go into `$VIRTUAL_ENV/bin`. You can also manually install patchelf from the
setup script with the following command:

```sh
$ python setup.py install_patchelf
```

If you'd prefer not to install patchelf at all, simply set the environment
variable `NO_PATCHELF` to `1` before installing bfg9000:

```sh
$ NO_PATCHELF=1 pip install .
```

## Installing MSBuild

Since many users don't need it, MSBuild support is an optional feature. To
install all the dependencies required for MSBuild, you can run the following:

```sh
$ pip install .[msbuild]
```
