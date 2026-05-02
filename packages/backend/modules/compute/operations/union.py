import sys

import runtime_compute.operations.union as _impl
from runtime_compute.operations.union import *  # noqa: F403

sys.modules[__name__] = _impl
