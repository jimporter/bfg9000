#ifndef INC_STATIC_B_HPP
#define INC_STATIC_B_HPP

#ifdef LIBSTATIC_B_STATIC
#  define STATIC_B_PUBLIC
#elif defined(_WIN32)
#  ifdef LIBSTATIC_B_EXPORTS
#    define STATIC_B_PUBLIC __declspec(dllexport)
#  else
#    define STATIC_B_PUBLIC __declspec(dllimport)
#  endif
#else
#  define STATIC_B_PUBLIC [[gnu::visibility("default")]]
#endif

namespace static_b {
  STATIC_B_PUBLIC void hello();
}

#endif
