#include "hello.hpp"

#include <iostream>
#include "inner.hpp"

namespace hello {
  void LIBHELLO_PUBLIC say_hello() {
    inner::use_ogg();
    std::cout << "hello, library!" << std::endl;
  }
}
