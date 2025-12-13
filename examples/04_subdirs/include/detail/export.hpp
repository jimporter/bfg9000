#ifndef INC_DETAIL_EXPORT_HPP
#define INC_DETAIL_EXPORT_HPP

#ifdef SUB_LIBLIBRARY_STATIC
#  define LIB_PUBLIC
#elif defined(_WIN32)
#  ifdef SUB_LIBLIBRARY_EXPORTS
#    define LIB_PUBLIC __declspec(dllexport)
#  else
#    define LIB_PUBLIC __declspec(dllimport)
#  endif
#else
#  define LIB_PUBLIC [[gnu::visibility("default")]]
#endif

#endif
