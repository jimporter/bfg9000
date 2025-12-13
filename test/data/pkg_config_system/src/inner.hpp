#ifndef INC_INNER_HPP
#define INC_INNER_HPP

#ifdef LIBINNER_STATIC
#  define LIBINNER_PUBLIC
#elif defined(_WIN32)
#  ifdef LIBINNER_EXPORTS
#    define LIBINNER_PUBLIC __declspec(dllexport)
#  else
#    define LIBINNER_PUBLIC __declspec(dllimport)
#  endif
#else
#  define LIBINNER_PUBLIC [[gnu::visibility("default")]]
#endif

namespace inner {
  LIBINNER_PUBLIC void use_ogg();
}

#endif
