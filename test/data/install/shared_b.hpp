#ifndef INC_SHARED_B_HPP
#define INC_SHARED_B_HPP

#ifdef LIBSHARED_B_STATIC
#  define SHARED_B_PUBLIC
#elif defined(_WIN32)
#  ifdef LIBSHARED_B_EXPORTS
#    define SHARED_B_PUBLIC __declspec(dllexport)
#  else
#    define SHARED_B_PUBLIC __declspec(dllimport)
#  endif
#else
#  define SHARED_B_PUBLIC [[gnu::visibility("default")]]
#endif

namespace shared_b {
  SHARED_B_PUBLIC void hello();
}

#endif
