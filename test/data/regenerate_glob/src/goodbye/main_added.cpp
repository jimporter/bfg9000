#include "english/goodbye.hpp"
#include "german/goodbye.hpp"
#include "french/goodbye.hpp"

int main() {
  english::say_goodbye();
  german::say_goodbye();
  french::say_goodbye();
  return 0;
}
