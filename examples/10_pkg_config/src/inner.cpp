#include "inner.hpp"

#include <ogg/ogg.h>

namespace inner {
  void LIBINNER_PUBLIC use_ogg() {
    ogg_sync_state state;

    ogg_sync_init(&state);
    ogg_sync_clear(&state);
  }
}
