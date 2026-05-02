import sys

import runtime_compute.manager as _impl
from runtime_compute.manager import *  # noqa: F403

sys.modules[__name__] = _impl
