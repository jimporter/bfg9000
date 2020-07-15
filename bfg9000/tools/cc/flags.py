from ... import options as opts

optimize_flags = {
    opts.OptimizeValue.disable : '-O0',
    opts.OptimizeValue.size    : '-Osize',
    opts.OptimizeValue.speed   : '-O3',
    opts.OptimizeValue.linktime: '-flto',
}
