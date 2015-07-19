import operator
import re
from cStringIO import StringIO
from collections import namedtuple, OrderedDict

from ... import path
from ... import safe_str
from ... import shell
from ... import iterutils

Path = path.Path

MakeInclude = namedtuple('MakeInclude', ['name', 'optional'])
MakeRule = namedtuple('MakeRule', ['targets', 'deps', 'order_only', 'recipe',
                                   'variables', 'phony'])

class MakeWriter(object):
    def __init__(self, stream):
        self.stream = stream

    @staticmethod
    def escape_str(string, syntax):
        def repl(match):
            return match.group(1) * 2 + '\\' + match.group(2)

        if '\n' in string:
            raise ValueError('illegal newline')
        result = string.replace('$', '$$')

        if syntax == 'target':
            return re.sub(r'(\\*)([#?*\[\]~\s%])', repl, result)
        elif syntax == 'dependency':
            return re.sub(r'(\\*)([#?*\[\]~\s|%])', repl, result)
        elif syntax == 'function':
            return re.sub(',', '$,', result)
        elif syntax == 'shell':
            return result
        else:
            raise ValueError("unknown syntax '{}'".format(syntax))

    def write_literal(self, string):
        self.stream.write(string)

    def write(self, thing, syntax, shell_quote=shell.quote_info):
        thing = safe_str.safe_str(thing)
        shelly = syntax in ['function', 'shell']
        escaped = False

        if isinstance(thing, safe_str.escaped_str):
            self.write_literal(thing.string)
            escaped = True
        elif isinstance(thing, basestring):
            if shelly and shell_quote:
                thing, escaped = shell_quote(thing)
            self.write_literal(self.escape_str(thing, syntax))
        elif isinstance(thing, safe_str.jbos):
            for i in thing.bits:
                escaped |= self.write(i, syntax, shell_quote)
        elif isinstance(thing, Path):
            out = MakeWriter(StringIO())
            thing = thing.realize(path_vars, shelly)
            escaped = out.write(thing, syntax, shell.escape)

            thing = out.stream.getvalue()
            if shelly and escaped:
                thing = shell.quote_escaped(thing)
            self.write_literal(thing)
        else:
            raise TypeError(type(thing))

        return escaped

    def write_each(self, things, syntax, delim=' ', prefix=None, suffix=None):
        for tween, i in iterutils.tween(things, delim, prefix, suffix):
            self.write_literal(i) if tween else self.write(i, syntax)

    def write_shell(self, thing):
        if iterutils.isiterable(thing):
            self.write_each(thing, 'shell')
        else:
            self.write(thing, 'shell', shell_quote=False)

class Pattern(object):
    def __init__(self, path):
        if len(re.findall(r'([^\\]|^)(\\\\)*%', path)) != 1:
            raise ValueError('exactly one % required')
        self.path = path

    def use(self):
        bits = re.split(r'%', self.path)
        delim = safe_str.escaped_str('%')
        return reduce(operator.add, iterutils.tween(bits, delim, flag=False))

    def _safe_str(self):
        return self.use()

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return repr(self.use())

    def __hash__(self):
        return hash(self.path)

    def __cmp__(self, rhs):
        return cmp(self.path, rhs.path)

    def __add__(self, rhs):
        return self.use() + rhs

    def __radd__(self, lhs):
        return lhs + self.use()

class MakeVariable(object):
    def __init__(self, name, quoted=False):
        self.name = re.sub(r'[\s:#=]', '_', name)
        self.quoted = quoted

    def use(self):
        fmt = '${}' if len(self.name) == 1 else '$({})'
        if self.quoted:
            fmt = shell.quote_escaped(fmt)
        return safe_str.escaped_str(fmt.format(self.name))

    def _safe_str(self):
        return self.use()

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return repr(self.use())

    def __hash__(self):
        return hash(self.name)

    def __cmp__(self, rhs):
        return cmp(self.name, rhs.name)

    def __add__(self, rhs):
        return self.use() + rhs

    def __radd__(self, lhs):
        return lhs + self.use()

class MakeFunc(object):
    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.args = args

    def use(self):
        out = MakeWriter(StringIO())
        prefix = '$(' + self.name + ' '
        for tween, i in iterutils.tween(self.args, ',', prefix, ')'):
            if tween:
                out.write_literal(i)
            else:
                out.write_each(iterutils.iterate(i), syntax='function')
        return safe_str.escaped_str(out.stream.getvalue())

    def _safe_str(self):
        return self.use()

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return repr(self.use())

class MakeCall(MakeFunc):
    def __init__(self, func, *args):
        if not isinstance(func, MakeVariable):
            func = MakeVariable(func)
        MakeFunc.__init__(self, 'call', func.name, *args)

path_vars = {
    Path.srcdir:     MakeVariable('srcdir'),
    Path.builddir:   None,
    Path.prefix:     MakeVariable('prefix'),
    Path.bindir:     MakeVariable('bindir'),
    Path.libdir:     MakeVariable('libdir'),
    Path.includedir: MakeVariable('includedir'),
}

class Makefile(object):
    def __init__(self):
        # TODO: Sort variables in some useful order.
        self._global_variables = OrderedDict()
        self._target_variables = OrderedDict({Pattern('%'): OrderedDict()})
        self._defines = OrderedDict()

        self._rules = []
        self._targets = set()
        self._includes = []

        # Necessary for escaping commas in function calls.
        self.variable(',', ',')

    def variable(self, name, value, flavor='simple', target=None):
        if not isinstance(name, MakeVariable):
            name = MakeVariable(name)
        if self.has_variable(name, target=target):
            raise ValueError("variable '{}' already exists".format(name.name))

        if flavor == 'define':
            self._defines[name] = value
        else:
            if target:
                if not target in self._target_variables:
                    self._target_variables[target] = OrderedDict()
                self._target_variables[target][name] = (value, flavor)
            else:
                self._global_variables[name] = (value, flavor)
        return name

    def has_variable(self, name, target=None):
        if not isinstance(name, MakeVariable):
            name = MakeVariable(name)
        if target:
            return (target in self._target_variables and
                    name in self._target_variables[target])
        else:
            return (name in self._global_variables or
                    name in self._defines)

    def include(self, name, optional=False):
        self._includes.append(MakeInclude(name, optional))

    def rule(self, target, deps=None, order_only=None, recipe=None,
             variables=None, phony=False):
        real_variables = {}
        if variables:
            for k, v in variables.iteritems():
                if not isinstance(k, MakeVariable):
                    k = MakeVariable(k)
                real_variables[k] = v

        targets = iterutils.listify(target)
        if len(targets) == 0:
            raise ValueError('must have at least one target')
        for i in targets:
            if self.has_rule(i):
                raise ValueError("rule for '{}' already exists".format(i))
            self._targets.add(i)
        self._rules.append(MakeRule(
            targets, iterutils.listify(deps), iterutils.listify(order_only),
            recipe, real_variables, phony
        ))

    def has_rule(self, name):
        return name in self._targets

    def _write_variable(self, out, name, value, flavor, target=None):
        operator = ' := ' if flavor == 'simple' else ' = '
        if target:
            out.write(target, syntax='target')
            out.write_literal(': ')
        out.write_literal(name.name + operator)
        out.write_shell(value)
        out.write_literal('\n')

    def _write_define(self, out, name, value):
        out.write_literal('define ' + name.name + '\n')
        for line in value:
            out.write_shell(line)
            out.write_literal('\n')
        out.write_literal('endef\n\n')

    def _write_rule(self, out, rule):
        if rule.variables:
            for target in rule.targets:
                for name, value in rule.variables.iteritems():
                    self._write_variable(out, name, value, 'simple',
                                         target=target)

        if rule.phony:
            out.write_literal('.PHONY: ')
            out.write_each(rule.targets, syntax='dependency')
            out.write_literal('\n')

        out.write_each(rule.targets, syntax='target')
        out.write_literal(':')
        out.write_each(rule.deps, syntax='dependency', prefix=' ')
        out.write_each(rule.order_only, syntax='dependency', prefix=' | ')

        if (isinstance(rule.recipe, MakeVariable) or
            isinstance(rule.recipe, MakeFunc)):
            out.write_literal(' ; ')
            out.write_shell(rule.recipe)
        elif rule.recipe is not None:
            for cmd in rule.recipe:
                out.write_literal('\n\t')
                out.write_shell(cmd)
        out.write_literal('\n\n')

    def write(self, out):
        out = MakeWriter(out)

        # Don't let make use built-in suffix rules.
        out.write_literal('.SUFFIXES:\n\n')

        for name, value in self._global_variables.iteritems():
            self._write_variable(out, name, value[0], value[1])
        if self._global_variables:
            out.write_literal('\n')

        newline = False
        for target, each in self._target_variables.iteritems():
            for name, value in each.iteritems():
                newline = True
                self._write_variable(out, name, value[0], value[1], target)
        if newline:
            out.write_literal('\n')

        for name, value in self._defines.iteritems():
            self._write_define(out, name, value)

        for r in self._rules:
            self._write_rule(out, r)

        for i in self._includes:
            out.write_literal(('-' if i.optional else '') + 'include ')
            out.write(i.name, syntax='target')
            out.write_literal('\n')
