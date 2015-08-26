#include <iostream>

#include <boost/program_options.hpp>

int main(int argc, const char *argv[]) {
  namespace opts = boost::program_options;

  opts::options_description desc;
  desc.add_options()
    ("hello", "say hello")
  ;

  opts::variables_map vm;
  opts::store(opts::parse_command_line(argc, argv, desc), vm);
  opts::notify(vm);

  if (vm.count("hello"))
    std::cout << "Hello, world!" << std::endl;
  return 0;
}
