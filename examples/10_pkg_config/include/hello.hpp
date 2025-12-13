#ifndef INC_HELLO_HPP
#define INC_HELLO_HPP

#ifdef LIBHELLO_STATIC
#  define LIBHELLO_PUBLIC
#elif defined(_WIN32)
#  ifdef LIBHELLO_EXPORTS
#    define LIBHELLO_PUBLIC __declspec(dllexport)
#  else
#    define LIBHELLO_PUBLIC __declspec(dllimport)
#  endif
#else
#  define LIBHELLO_PUBLIC [[gnu::visibility("default")]]
#endif

namespace hello {
  LIBHELLO_PUBLIC void say_hello();
}

#endif
