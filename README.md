# bfg9000 - build file generator

[![PyPi version][pypi-image]][pypi-link]
[![Documentation][documentation-image]][documentation-link]
[![Travis build status][travis-image]][travis-link]
[![Appveyor build status][appveyor-image]][appveyor-link]

**bfg9000** is a cross-platform *build configuration system* with an emphasis on
making it easy to define how to build your software. It converts a Python-based
build script into the appropriate files for your underlying build system of
choice (Ninja, Make, or MSBuild).

## Why bfg9000?

#### Already familiar

`build.bfg` files are just Python scripts with some new functions added, so you
may already know how to write them; and when your build gets complicated, you
can rely on the existing Python ecosystem to get you out of trouble.

#### Build fast

Python may be slow, but bfg9000 gets out of the way as quickly as possible and
relies on existing, mature build systems like Make and Ninja to do the heavy
lifting of building your software.

#### Stay sane

Building your code shouldn't be the hard part of developing your project. Above
all else, bfg9000 strives to make it easy to write your build scripts.

## A brief example

You can't get much simpler than the simplest `build.bfg` file:

```python
executable('simple', files=['simple.cpp'])
```

To build this executable, we need to create the actual build files and then
run them:

```sh
$ cd /path/to/src/
$ 9k build/
$ cd build/
$ ninja
```

From there, you can run your newly-created executable: `./simple`. Hooray!

For further examples, please see the
[`examples/`](https://github.com/jimporter/bfg9000/tree/master/examples)
subdirectory.

# Installation

bfg9000 uses [setuptools](https://pythonhosted.org/setuptools/), so installation
is much the same as any other Python package:

```sh
$ pip install bfg9000
```

From there, you can start using bfg to build your software! For more information
about how to install bfg9000, see the
[documentation](https://jimporter.github.io/bfg9000/install).

## License

This project is licensed under the BSD 3-clause license.

[pypi-image]: https://img.shields.io/pypi/v/bfg9000.svg
[pypi-link]: https://pypi.python.org/pypi/bfg9000
[documentation-image]: https://img.shields.io/badge/docs-bfg9000-blue.svg
[documentation-link]: https://jimporter.github.io/bfg9000/
[travis-image]: https://travis-ci.org/jimporter/bfg9000.svg?branch=master
[travis-link]: https://travis-ci.org/jimporter/bfg9000
[appveyor-image]: https://ci.appveyor.com/api/projects/status/hxvbggf6exq8i2k6/branch/master?svg=true
[appveyor-link]: https://ci.appveyor.com/project/jimporter/bfg9000/branch/master
