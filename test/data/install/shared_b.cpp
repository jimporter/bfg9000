#include "shared_b.hpp"

#include <iostream>

SHARED_B_PUBLIC void shared_b::hello() {
  std::cout << "hello from shared b!" << std::endl;
}
