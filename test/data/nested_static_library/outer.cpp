#include "middle.hpp"

#include <iostream>

namespace outer {
  void hello() {
    middle::hello();
    std::cout << "hello from outer" << std::endl;
  }
}
