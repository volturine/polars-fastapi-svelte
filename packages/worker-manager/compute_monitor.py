import sys

import runtime_compute.monitor as _impl
from runtime_compute.monitor import *  # noqa: F403

sys.modules[__name__] = _impl
