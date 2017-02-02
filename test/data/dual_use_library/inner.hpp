#ifndef INC_INNER_HPP
#define INC_INNER_HPP

#if defined(_WIN32) && !defined(LIBINNER_STATIC)
#  ifdef LIBINNER_EXPORTS
#    define LIBINNER_PUBLIC __declspec(dllexport)
#  else
#    define LIBINNER_PUBLIC __declspec(dllimport)
#  endif
#else
#  define LIBINNER_PUBLIC
#endif

namespace inner {
  void LIBINNER_PUBLIC hello();
}

#endif
