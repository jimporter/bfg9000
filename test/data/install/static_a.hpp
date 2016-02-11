#ifndef INC_STATIC_A_HPP
#define INC_STATIC_A_HPP

#if defined(_WIN32) && !defined(LIBSTATIC_A_STATIC)
#  ifdef LIBSTATIC_A_EXPORTS
#    define STATIC_A_PUBLIC __declspec(dllexport)
#  else
#    define STATIC_A_PUBLIC __declspec(dllimport)
#  endif
#else
#  define STATIC_A_PUBLIC
#endif

namespace static_a {
  void STATIC_A_PUBLIC hello();
}

#endif
