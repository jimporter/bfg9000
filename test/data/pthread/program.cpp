#include <iostream>
#include <pthread.h>

void * thread_func(void *) {
  std::cout << "hello from thread!" << std::endl;
  pthread_exit(0);
}

int main() {
  pthread_t thread;
  if(pthread_create(&thread, 0, thread_func, 0)) {
    std::cerr << "error creating thread" << std::endl;
    return 1;
  }

  pthread_exit(0);
}
