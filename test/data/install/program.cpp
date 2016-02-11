#include "shared_a.hpp"
#include "shared_b.hpp"
#include "static_a.hpp"
#include "static_b.hpp"

int main() {
  shared_a::hello();
  shared_b::hello();
  static_a::hello();
  static_b::hello();
  return 0;
}
