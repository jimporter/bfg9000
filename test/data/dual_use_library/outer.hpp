#ifndef INC_OUTER_HPP
#define INC_OUTER_HPP

#ifdef LIBOUTER_STATIC
#  define LIBOUTER_PUBLIC
#elif defined(_WIN32)
#  ifdef LIBOUTER_EXPORTS
#    define LIBOUTER_PUBLIC __declspec(dllexport)
#  else
#    define LIBOUTER_PUBLIC __declspec(dllimport)
#  endif
#else
#  define LIBOUTER_PUBLIC [[gnu::visibility("default")]]
#endif

namespace outer {
  LIBOUTER_PUBLIC void hello();
}

#endif
