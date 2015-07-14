#ifndef INC_LIBRARY_HPP
#define INC_LIBRARY_HPP

#if defined(_WIN32)
#  ifdef _WINDLL
#    define LIB_PUBLIC __declspec(dllexport)
#  else
#    define LIB_PUBLIC __declspec(dllimport)
#  endif
#else
#  define LIB_PUBLIC
#endif

void LIB_PUBLIC hello();

#endif
