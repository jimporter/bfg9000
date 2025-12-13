#ifndef INC_STATIC_A_HPP
#define INC_STATIC_A_HPP

#ifdef LIBSTATIC_A_STATIC
#  define STATIC_A_PUBLIC
#elif defined(_WIN32)
#  ifdef LIBSTATIC_A_EXPORTS
#    define STATIC_A_PUBLIC __declspec(dllexport)
#  else
#    define STATIC_A_PUBLIC __declspec(dllimport)
#  endif
#else
#  define STATIC_A_PUBLIC [[gnu::visibility("default")]]
#endif

namespace static_a {
  STATIC_A_PUBLIC void hello();
}

#endif
