#include <cstdlib>
#include <string>

int main() {
  const char *val = std::getenv("VARIABLE");
  return val && val == std::string("hello world") ? 0 : 1;
}
