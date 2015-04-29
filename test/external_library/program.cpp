#include <zlib.h>

int main() {
  gzFile f = gzopen("file.gz", "w");
  gzclose(f);
  return 0;
}
