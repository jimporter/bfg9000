#include "static_b.hpp"

#include <iostream>

STATIC_B_PUBLIC void static_b::hello() {
  std::cout << "hello from static b!" << std::endl;
}
