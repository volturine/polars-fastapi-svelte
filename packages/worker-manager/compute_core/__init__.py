import sys

import runtime_compute.core as _impl
from runtime_compute.core import *  # noqa: F403

sys.modules[__name__] = _impl
