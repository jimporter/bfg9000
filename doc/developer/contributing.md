# Contributing

So, you've found an issue with bfg9000 or have an idea to improve it? Great!
This page will provide you with some useful information to help you get started.

## Filing an issue

Before contributing a patch, it's best to [file an issue][new-issue] to discuss
your plan. This will help ensure that you've got a good idea of the best way to
go about things and don't go down the wrong path to start.

## Setting up a development environment

Like most other Python-based projects, the easiest way to set up a development
environment for bfg9000 is to use `pip` to install an editable version of the
package. You'll probably also want all the testing dependencies, which you can
install with the `test` extra:

```sh
$ pip install -e '.[test]'
```

### Running tests

bfg9000 has a suite of tests to ensure that everything works properly. (Well,
everything that has tests!) As you may expect, you can run these via:

```sh
$ python setup.py test
```

If you'd like to run a subset of tests, such as when trying to fix a bug in a
specific area of the code, you can limit the tests that get run. For instance,
to run only the tests in `test/integration/test_simple.py`, you can type:

```sh
$ python setup.py test -s test.integration.test_simple
```

To generate a coverage report, simply replace `test` with `coverage`, and build
the report in the format you want, e.g.:

```sh
$ python setup.py coverage && coverage html
```

### Linting code

bfg9000 uses [flake8][flake8] for linting. You can check this with the `lint`
command like so:

```sh
$ python setup.py lint
```

[new-issue]: https://github.com/jimporter/bfg9000/issues/new
[flake8]: https://flake8.readthedocs.org/en/latest/
