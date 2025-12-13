#ifndef INC_LIBRARY_HPP
#define INC_LIBRARY_HPP

#ifdef LIBLIBRARY_STATIC
#  define LIB_PUBLIC
#elif defined(_WIN32)
#  ifdef LIBLIBRARY_EXPORTS
#    define LIB_PUBLIC __declspec(dllexport)
#  else
#    define LIB_PUBLIC __declspec(dllimport)
#  endif
#else
#  define LIB_PUBLIC [[gnu::visibility("default")]]
#endif

LIB_PUBLIC void hello();

#endif
