#ifndef INC_SHARED_A_HPP
#define INC_SHARED_A_HPP

#ifdef LIBSHARED_A_STATIC
#  define SHARED_A_PUBLIC
#elif defined(_WIN32)
#  ifdef LIBSHARED_A_EXPORTS
#    define SHARED_A_PUBLIC __declspec(dllexport)
#  else
#    define SHARED_A_PUBLIC __declspec(dllimport)
#  endif
#else
#  define SHARED_A_PUBLIC [[gnu::visibility("default")]]
#endif

namespace shared_a {
  SHARED_A_PUBLIC void hello();
}

#endif
