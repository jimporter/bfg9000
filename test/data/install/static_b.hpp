#ifndef INC_STATIC_B_HPP
#define INC_STATIC_B_HPP

#if defined(_WIN32) && !defined(LIBSTATIC_B_STATIC)
#  ifdef LIBSTATIC_B_EXPORTS
#    define STATIC_B_PUBLIC __declspec(dllexport)
#  else
#    define STATIC_B_PUBLIC __declspec(dllimport)
#  endif
#else
#  define STATIC_B_PUBLIC
#endif

namespace static_b {
  void STATIC_B_PUBLIC hello();
}

#endif
