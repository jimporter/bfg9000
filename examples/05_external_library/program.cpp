#include <ogg/ogg.h>

int main() {
  ogg_sync_state state;

  ogg_sync_init(&state);
  ogg_sync_clear(&state);

  return 0;
}
