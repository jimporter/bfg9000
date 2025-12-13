#include "library.hpp"

#include <iostream>
#include <string>

void hello(const char *name) {
  std::cout << "Hello, " << name << std::string(ENTHUSIASM, '!') << std::endl;
}
