#ifndef INC_DETAIL_EXPORT_HPP
#define INC_DETAIL_EXPORT_HPP

#if defined(_WIN32) && !defined(SUB_LIBLIBRARY_STATIC)
#  ifdef SUB_LIBLIBRARY_EXPORTS
#    define LIB_PUBLIC __declspec(dllexport)
#  else
#    define LIB_PUBLIC __declspec(dllimport)
#  endif
#else
#  define LIB_PUBLIC
#endif

#endif
