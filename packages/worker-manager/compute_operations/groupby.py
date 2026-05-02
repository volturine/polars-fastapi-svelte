import sys

import runtime_compute.operations.groupby as _impl
from runtime_compute.operations.groupby import *  # noqa: F403

sys.modules[__name__] = _impl
