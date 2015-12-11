# Reference

## Build steps

### alias(*name*, [*deps*])

### command(*name*, [*cmd*|*cmds*], [*environment*], [*extra_deps*])

### executable(*name*, [*files*, [*include*], [*libs*], [*packages*], [*compile_options*], [*link_options*], [*lang*], [*extra_deps*]])

### header(*name*)

### header_directory(*directory*)

### object_file([*name*], [*file*, [*include*], [*packages*], [*options*], [*lang*], [*extra_deps*]])

### object_files(*files*[, *include*], [*packages*], [*options*], [*lang*], [*extra_deps*])

### shared_library(*name*[, *files*, [*include*], [*libs*], [*packages*], [*compile_options*], [*link_options*], [*lang*], [*extra_deps*]])

### source_file(*name*[, *lang*])

### static_library(*name*[, *files*, [*include*], [*libs*], [*packages*], [*compile_options*], [*link_options*], [*lang*], [*extra_deps*]])

## Other rules

### default(*...*)

### global_options(*options*, *lang*)

### global_link_options(*options*)

### install(*...*, [*all*])

### test(*test*, [*options*], [*environment*], [*driver*])

### test_driver(*driver*, [*options*], [*environment*], [*parent*])

### test_deps(*...*)

## Package finders

### boost_package([*name*], [*version*])

### system_executable(*name*)

### system_package(*name*)

## Miscellaneous

### bfg9000_required_version([*version*], [*python_version*])

### filter_by_platform(*name*, *type*)

### find_files([*path*], [*name*], [*type*], [*flat*], [*filter*], [*cache*])
