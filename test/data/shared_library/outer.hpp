#ifndef INC_OUTER_HPP
#define INC_OUTER_HPP

#if defined(_WIN32) && !defined(OUTER_LIBOUTER_STATIC)
#  ifdef OUTER_LIBOUTER_EXPORTS
#    define LIBOUTER_PUBLIC __declspec(dllexport)
#  else
#    define LIBOUTER_PUBLIC __declspec(dllimport)
#  endif
#else
#  define LIBOUTER_PUBLIC
#endif

namespace outer {
  void LIBOUTER_PUBLIC hello();
}

#endif
