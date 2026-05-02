import sys

import runtime_compute.operations as _impl
from runtime_compute.operations import *  # noqa: F403

sys.modules[__name__] = _impl
