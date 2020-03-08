#ifndef INC_HELLO_HPP
#define INC_HELLO_HPP

#if defined(_WIN32) && !defined(LIBHELLO_STATIC)
#  ifdef LIBHELLO_EXPORTS
#    define LIBHELLO_PUBLIC __declspec(dllexport)
#  else
#    define LIBHELLO_PUBLIC __declspec(dllimport)
#  endif
#else
#  define LIBHELLO_PUBLIC
#endif

namespace hello {
  void LIBHELLO_PUBLIC say_hello();
}

#endif
