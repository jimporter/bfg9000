#include "middle.hpp"
#include "inner.hpp"

#include <iostream>

namespace middle {
  void hello() {
    inner::hello();
  }
}
