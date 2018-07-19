#ifndef INC_LIBRARY_H
#define INC_LIBRARY_H

#if defined(_WIN32)
#  ifdef LIBSTATIC_STATIC
#    define LIB_PUBLIC __declspec(dllexport)
#  else
#    define LIB_PUBLIC __declspec(dllimport)
#  endif
#else
#  define LIB_PUBLIC
#endif

#ifdef __cplusplus
extern "C"
#endif
LIB_PUBLIC void hello();

#endif
