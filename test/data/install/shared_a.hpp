#ifndef INC_SHARED_A_HPP
#define INC_SHARED_A_HPP

#if defined(_WIN32) && !defined(LIBSHARED_A_STATIC)
#  ifdef LIBSHARED_A_EXPORTS
#    define SHARED_A_PUBLIC __declspec(dllexport)
#  else
#    define SHARED_A_PUBLIC __declspec(dllimport)
#  endif
#else
#  define SHARED_A_PUBLIC
#endif

namespace shared_a {
  void SHARED_A_PUBLIC hello();
}

#endif
