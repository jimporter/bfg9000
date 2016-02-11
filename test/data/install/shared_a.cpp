#include "shared_a.hpp"

#include <iostream>

void SHARED_A_PUBLIC shared_a::hello() {
  std::cout << "hello from shared a!" << std::endl;
}
