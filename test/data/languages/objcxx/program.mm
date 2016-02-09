#import <iostream>

@interface Hello {}
- (void)hello;
@end

int main(int argc, char *argv[]) {
  std::cout << "hello from objective c++!" << std::endl;
  return 0;
}
