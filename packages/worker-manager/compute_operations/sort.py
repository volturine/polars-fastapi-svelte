import sys

import runtime_compute.operations.sort as _impl
from runtime_compute.operations.sort import *  # noqa: F403

sys.modules[__name__] = _impl
