#include <fstream>
#include <iostream>
#include <string>

int main() {
  std::string line;
  std::ifstream f("dir/data.txt");
  std::getline(f, line);

  std::cout << line << std::endl;
  return 0;
}
