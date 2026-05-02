import sys

import runtime_compute.operations.ai as _impl
from runtime_compute.operations.ai import *  # noqa: F403

sys.modules[__name__] = _impl
