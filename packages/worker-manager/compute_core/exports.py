import sys

import runtime_compute.core.exports as _impl
from runtime_compute.core.exports import *  # noqa: F403

sys.modules[__name__] = _impl
