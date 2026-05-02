import sys

import runtime_compute.operations.rename as _impl
from runtime_compute.operations.rename import *  # noqa: F403

sys.modules[__name__] = _impl
