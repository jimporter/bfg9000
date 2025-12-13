#ifndef INC_MIDDLE_HPP
#define INC_MIDDLE_HPP

#ifdef LIBMIDDLE_STATIC
#  define LIBMIDDLE_PUBLIC
#elif defined(_WIN32)
#  ifdef LIBMIDDLE_EXPORTS
#    define LIBMIDDLE_PUBLIC __declspec(dllexport)
#  else
#    define LIBMIDDLE_PUBLIC __declspec(dllimport)
#  endif
#else
#  define LIBMIDDLE_PUBLIC [[gnu::visibility("default")]]
#endif

namespace middle {
  LIBMIDDLE_PUBLIC void hello();
}

#endif
