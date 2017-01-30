#include "inner.hpp"

#include <iostream>

namespace middle {
  void hello() {
    inner::hello();
    std::cout << "hello from middle" << std::endl;
  }
}
