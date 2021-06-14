import argparse

hello_src = """
#include <iostream>

int main() {
  std::cout << "hello from python!" << std::endl;
  return 0;
}
"""

intro_src = """
#include <iostream>

int main() {{
  std::cout << "my name is {}!" << std::endl;
  return 0;
}}
"""

goodbye_hdr = """
#ifndef INC_GOODBYE_HPP
#define INC_GOODBYE_HPP

void goodbye();

#endif
"""

goodbye_src = """
#include "goodbye.hpp"

#include <iostream>

void goodbye() {
  std::cout << "goodbye from python!" << std::endl;
}
"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    hello_p = subparsers.add_parser('hello')
    hello_p.add_argument('file')

    introduce_p = subparsers.add_parser('introduce')
    introduce_p.add_argument('file')
    introduce_p.add_argument('namefile')

    goodbye_p = subparsers.add_parser('goodbye')
    goodbye_p.add_argument('header')
    goodbye_p.add_argument('source')

    args = parser.parse_args()

    if args.command == 'hello':
        with open(args.file, 'w') as f:
            f.write(hello_src)
    elif args.command == 'introduce':
        with open(args.namefile) as f:
            name = f.read().strip()
        with open(args.file, 'w') as f:
            f.write(intro_src.format(name))
    else:
        with open(args.header, 'w') as f:
            f.write(goodbye_hdr)
        with open(args.source, 'w') as f:
            f.write(goodbye_src)
