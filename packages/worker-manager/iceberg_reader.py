import sys

import runtime_compute.iceberg_reader as _impl
from runtime_compute.iceberg_reader import *  # noqa: F403

sys.modules[__name__] = _impl
