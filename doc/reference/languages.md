# Supported Languages

bfg9000 supports the following languages. In the tables below, you'll find the
language name as it's used internally (which can be passed via the `lang`
parameter where applicable), the automatically-detected file extensions, and the
build steps that can be used with that language.

---

### C

Name
: `'c'`

Source extensions
: `.c`

Header extensions
: `.h`

Build steps
: [*object_file*](builtins.md#object_file),
  [*executable*](builtins.md#executable),
  [*shared_library*](builtins.md#shared_library),
  [*static_library*](builtins.md#static_library)

### C++

Name
: `'c++'`

Source extensions
: `.cpp`, `.cc`, `.cp`, `.cxx`, `.CPP`, `.c++`, `.C`

Header extensions
: `.hpp`, `.hh`, `.hp`, `.hxx`, `.HPP`, `.h++`, `.H`

Build steps
: [*object_file*](builtins.md#object_file),
  [*executable*](builtins.md#executable),
  [*shared_library*](builtins.md#shared_library),
  [*static_library*](builtins.md#static_library)

### Objective C

Name
: `'objc'`

Source extensions
: `.m`

Build steps
: [*object_file*](builtins.md#object_file),
  [*executable*](builtins.md#executable),
  [*shared_library*](builtins.md#shared_library),
  [*static_library*](builtins.md#static_library)

### Objective C++

Name
: `'objc++'`

Source extensions
: `.mm`, `.M`

Build steps
: [*object_file*](builtins.md#object_file),
  [*executable*](builtins.md#executable),
  [*shared_library*](builtins.md#shared_library),
  [*static_library*](builtins.md#static_library)

### Fortran 77

Name
: `'f77'`

Source extensions
: `.f`, `.for`, `.ftn`

Build steps
: [*object_file*](builtins.md#object_file),
  [*executable*](builtins.md#executable),
  [*shared_library*](builtins.md#shared_library),
  [*static_library*](builtins.md#static_library)

### Fortran 95

Name
: `'f95'`

Source extensions
: `.f90`, `.f95`, `.f03`, `.f08`

Build steps
: [*object_file*](builtins.md#object_file),
  [*executable*](builtins.md#executable),
  [*shared_library*](builtins.md#shared_library),
  [*static_library*](builtins.md#static_library)

Notes
: Modules not supported

### Java

Name
: `'java'`

Source extensions
: `.java`

Build steps
: [*object_file*](builtins.md#object_file),
  [*executable*](builtins.md#executable),
  [*shared_library*](builtins.md#shared_library),
  [*static_library*](builtins.md#static_library) (GCJ only)

### Scala

Name
: `'scala'`

Source extensions
: `.scala`

Build steps
: [*object_file*](builtins.md#object_file),
  [*executable*](builtins.md#executable),
  [*shared_library*](builtins.md#shared_library)

### Lex

Name
: `'lex'`

Source extensions
: `.l`

Build steps
: [*generated_source*](builtins.md#generated_source)

### Yacc

Name
: `'yacc'`

Source extensions
: `.y`

Build steps
: [*generated_source*](builtins.md#generated_source)

### Windows Resource

Name
: `'rc'`

Source extensions
: `.rc`

Build steps
: [*object_file*](builtins.md#object_file)

### Qt MOC

Name
: `'qtmoc'`

Source extensions
: *none*

Build steps
: [*generated_source*](builtins.md#generated_source)

### Qt Resource

Name
: `'qrc'`

Source extensions
: `.qrc`

Build steps
: [*generated_source*](builtins.md#generated_source)

### Qt UI

Name
: `'qtui'`

Source extensions
: `.ui`

Build steps
: [*generated_source*](builtins.md#generated_source)

### Lua

Name
: `'lua'`

Source extensions
: `.lua`

Build steps
: *none*

### Perl

Name
: `'perl'`

Source extensions
: `.pl`

Build steps
: *none*

### Python

Name
: `'python'`

Source extensions
: `.py`

Build steps
: *none*

### Ruby

Name
: `'ruby'`

Source extensions
: `.rb`

Build steps
: *none*
