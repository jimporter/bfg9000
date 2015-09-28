#include <cstdlib>
#include <string>

int main() {
  const char *val = std::getenv("VARIABLE");
  return val ? 1 : 0;
}
