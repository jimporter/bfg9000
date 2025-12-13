#include "library.hpp"

#include <iostream>
#include <string>

LIB_PUBLIC void hello(const char *name) {
  std::cout << "Hello, " << name << std::string(ENTHUSIASM, '!') << std::endl;
}
