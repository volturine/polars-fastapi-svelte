import sys

import runtime_compute.operations.sample as _impl
from runtime_compute.operations.sample import *  # noqa: F403

sys.modules[__name__] = _impl
