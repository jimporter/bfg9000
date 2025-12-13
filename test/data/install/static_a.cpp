#include "static_a.hpp"

#include <iostream>

STATIC_A_PUBLIC void static_a::hello() {
  std::cout << "hello from static a!" << std::endl;
}
