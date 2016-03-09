#include <iostream>

extern "C"
void echo_(const char *msg, int len) {
  std::cout << msg << std::endl;
}
