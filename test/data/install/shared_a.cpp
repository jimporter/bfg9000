#include "shared_a.hpp"

#include <iostream>

SHARED_A_PUBLIC void shared_a::hello() {
  std::cout << "hello from shared a!" << std::endl;
}
