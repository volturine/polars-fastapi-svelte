import sys

import runtime_compute.operations.timeseries as _impl
from runtime_compute.operations.timeseries import *  # noqa: F403

sys.modules[__name__] = _impl
