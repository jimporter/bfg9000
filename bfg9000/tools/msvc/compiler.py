from itertools import chain

from ... import options as opts, safe_str
from ..common import BuildCommand
from ...arguments.windows import ArgumentParser
from ...builtins.file_types import make_immediate_file
from ...file_types import (HeaderDirectory, MsvcPrecompiledHeader, ObjectFile,
                           SourceFile)
from ...iterutils import iterate, listify
from ...languages import known_langs
from ...objutils import memoize
from ...path import Path

_warning_flags = {
    opts.WarningValue.disable: '/w',
    opts.WarningValue.all    : '/W3',
    opts.WarningValue.extra  : '/W4',
    opts.WarningValue.error  : '/WX',
}

_optimize_flags = {
    opts.OptimizeValue.disable : '/Od',
    opts.OptimizeValue.size    : '/O1',
    opts.OptimizeValue.speed   : '/O2',
    opts.OptimizeValue.linktime: '/GL',
}


class MsvcBaseCompiler(BuildCommand):
    @property
    def deps_flavor(self):
        return 'msvc'

    @property
    def needs_libs(self):
        return False

    @property
    def needs_package_options(self):
        return True

    def search_dirs(self, strict=False):
        cpath = self.env.variables.getpaths('CPATH')
        include = self.env.variables.getpaths('INCLUDE')
        return cpath + include

    def _call(self, cmd, input, output, deps=None, flags=None):
        result = list(chain( cmd, self._always_flags, iterate(flags) ))
        if deps:
            result.append('/showIncludes')
        result.extend(['/c', input, '/Fo' + output])
        return result

    @property
    def _always_flags(self):
        return ['/nologo', '/EHsc']

    def flags(self, options, global_options=None, output=None, mode='normal'):
        syntax = 'cc' if mode == 'pkg-config' else 'msvc'
        debug = static = False
        flags = []
        for i in options:
            if isinstance(i, opts.include_dir):
                prefix = '-I' if syntax == 'cc' else '/I'
                flags.append(prefix + i.directory.path)
            elif isinstance(i, opts.define):
                prefix = '-D' if syntax == 'cc' else '/D'
                if i.value:
                    flags.append(prefix + i.name + '=' + i.value)
                else:
                    flags.append(prefix + i.name)
            elif isinstance(i, opts.std):
                flags.append('/std:' + i.value)
            elif isinstance(i, opts.warning):
                for j in i.value:
                    flags.append(_warning_flags[j])
            elif isinstance(i, opts.debug):
                debug = True
                flags.append('/Zi')
            elif isinstance(i, opts.static):
                static = True
            elif isinstance(i, opts.optimize):
                for j in i.value:
                    flags.append(_optimize_flags[j])
            elif isinstance(i, opts.pch):
                flags.append('/Yu' + i.header.header_name)
            elif isinstance(i, opts.sanitize):
                flags.append('/RTC1')
            elif isinstance(i, safe_str.stringy_types):
                flags.append(i)
            else:
                raise TypeError('unknown option type {!r}'.format(type(i)))

        for i in global_options or []:
            if isinstance(i, opts.debug):
                debug = True
            elif isinstance(i, opts.static):
                static = True

        if mode == 'normal':
            flags.append('/M{link}{debug}'.format(link='T' if static else 'D',
                                                  debug='d' if debug else ''))
        return flags

    @staticmethod
    @memoize
    def __parser():
        parser = ArgumentParser()
        parser.add('/nologo')
        parser.add('/D', '-D', type=list, dest='defines')
        parser.add('/I', '-I', type=list, dest='includes')

        warn = parser.add('/W', type=dict, dest='warnings')
        warn.add('0', '1', '2', '3', '4', 'all', dest='level')
        warn.add('X', type=bool, dest='as_error')
        warn.add('X-', type=bool, dest='as_error', value=False)
        parser.add('/w', type='alias', base=warn, value='0')

        pch = parser.add('/Y', type=dict, dest='pch')
        pch.add('u', type=str, dest='use')
        pch.add('c', type=str, dest='create')

        parser.add('/Z7', value='old', dest='debug')
        parser.add('/Zi', value='pdb', dest='debug')
        parser.add('/ZI', value='edit', dest='debug')

        parser.add('/MT', value='static', dest='runtime')
        parser.add('/MTd', value='static-debug', dest='runtime')
        parser.add('/MD', value='dynamic', dest='runtime')
        parser.add('/MDd', value='dynamic-debug', dest='runtime')

        return parser

    def parse_flags(self, flags):
        result, extra = self.__parser().parse_known(flags)
        result['extra'] = extra
        return result


class MsvcCompiler(MsvcBaseCompiler):
    def __init__(self, builder, env, *, command, flags):
        super().__init__(builder, env, command=command, flags=flags)

    @property
    def accepts_pch(self):
        return True

    def default_name(self, input, step):
        return input.path.stripext().suffix

    def output_file(self, name, step):
        pch = getattr(step, 'pch', None)
        output = ObjectFile(Path(name + '.obj'),
                            self.builder.object_format, self.lang)
        if pch:
            output.extra_objects = [pch.object_file]
        return output


class MsvcPchCompiler(MsvcBaseCompiler):
    def __init__(self, builder, env, *, command, flags):
        super().__init__(builder, env, command[0] + '_pch', command=command,
                         flags=flags)

    @property
    def num_outputs(self):
        return 2

    @property
    def accepts_pch(self):
        # You can't to pass a PCH to a PCH compiler!
        return False

    def _call(self, cmd, input, output, deps=None, flags=None):
        output = listify(output)
        result = super()._call(cmd, input, output[1], deps, flags)
        result.append('/Fp' + output[0])
        return result

    def pre_output(self, context, name, step):
        header = getattr(step, 'file')
        options = opts.option_list()

        if step.pch_source is None:
            ext = known_langs[self.lang].default_ext('source')
            basename = header.path.stripext(ext).basename()
            step.pch_source = SourceFile(Path(name).parent().append(basename),
                                         header.lang)
            with make_immediate_file(context, step.pch_source) as out:
                out.write('#include "{}"\n'.format(header.path.basename()))

            # Add the include path for the header to ensure the PCH source
            # finds it.
            d = HeaderDirectory(header.path.parent())
            options.append(opts.include_dir(d))

        # Add flag to create PCH file.
        options.append('/Yc' + header.path.suffix)
        return options

    def default_name(self, input, step):
        return input.path.suffix

    def output_file(self, name, step):
        pchpath = Path(name).stripext('.pch')
        objpath = step.pch_source.path.stripext('.obj').reroot()
        output = MsvcPrecompiledHeader(
            pchpath, objpath, name, self.builder.object_format, self.lang
        )
        return [output, output.object_file]
