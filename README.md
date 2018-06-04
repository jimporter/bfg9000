# bfg9000 - build file generator

[![PyPi version][pypi-image]][pypi-link]
[![Documentation][documentation-image]][documentation-link]
[![Travis build status][travis-image]][travis-link]
[![Appveyor build status][appveyor-image]][appveyor-link]
[![Coverage status][codecov-image]][codecov-link]

**bfg9000** is a cross-platform *build configuration system* with an emphasis on
making it easy to define how to build your software. It converts a Python-based
build script into the appropriate files for your underlying build system of
choice (Ninja, Make, or MSBuild).

## Why bfg9000?

#### Familiar syntax

`build.bfg` files are just Python scripts with some new functions added, so you
may already know how to write them; and when your build gets complicated, you
can rely on the existing Python ecosystem to get you out of trouble.

#### Fast builds

bfg9000 ensures your builds are fast by relying on existing, mature build
systems like Make and Ninja to do the heavy lifting of building your software;
often, incremental builds don't need to execute bfg9000 at all!

#### Stay sane

Building your code shouldn't be the hard part of developing your project. Above
all else, bfg9000 strives to help you get your build right the *first* time with
many helpful [features][features].

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

For further examples, please see the [`examples/`][examples] subdirectory.

## Installation

bfg9000 uses [setuptools][setuptools], so installation is much the same as any
other Python package:

```sh
$ pip install bfg9000
```

From there, you can start using bfg to build your software! (If you're using
Ubuntu, you can also install bfg9000 from the following PPA:
[ppa:jimporter/stable][ppa]). For more information about how to install bfg9000,
see the [documentation][getting-started].

## License

This project is licensed under the [BSD 3-clause license](LICENSE).

[pypi-image]: https://img.shields.io/pypi/v/bfg9000.svg
[pypi-link]: https://pypi.python.org/pypi/bfg9000
[documentation-image]: https://img.shields.io/badge/docs-bfg9000-blue.svg
[documentation-link]: https://jimporter.github.io/bfg9000/
[travis-image]: https://travis-ci.org/jimporter/bfg9000.svg?branch=master
[travis-link]: https://travis-ci.org/jimporter/bfg9000
[appveyor-image]: https://ci.appveyor.com/api/projects/status/hxvbggf6exq8i2k6/branch/master?svg=true
[appveyor-link]: https://ci.appveyor.com/project/jimporter/bfg9000/branch/master
[codecov-image]: https://codecov.io/gh/jimporter/bfg9000/branch/master/graph/badge.svg
[codecov-link]: https://codecov.io/gh/jimporter/bfg9000

[features]: https://jimporter.github.io/bfg9000/latest/user/features
[examples]: https://github.com/jimporter/bfg9000/tree/master/examples
[setuptools]: https://pythonhosted.org/setuptools/
[ppa]: https://launchpad.net/~jimporter/+archive/ubuntu/stable
[getting-started]: https://jimporter.github.io/bfg9000/latest/getting-started
