#include "outer.hpp"
#include "middle.hpp"

#include <iostream>

namespace outer {
  void hello() {
    middle::hello();
  }
}
