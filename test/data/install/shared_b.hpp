#ifndef INC_SHARED_B_HPP
#define INC_SHARED_B_HPP

#if defined(_WIN32) && !defined(LIBSHARED_B_STATIC)
#  ifdef LIBSHARED_B_EXPORTS
#    define SHARED_B_PUBLIC __declspec(dllexport)
#  else
#    define SHARED_B_PUBLIC __declspec(dllimport)
#  endif
#else
#  define SHARED_B_PUBLIC
#endif

namespace shared_b {
  void SHARED_B_PUBLIC hello();
}

#endif
