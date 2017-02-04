#include <ogg/ogg.h>

namespace inner {
  void use_ogg() {
    ogg_sync_state state;

    ogg_sync_init(&state);
    ogg_sync_clear(&state);
  }
}
