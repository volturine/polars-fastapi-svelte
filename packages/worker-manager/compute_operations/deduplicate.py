import sys

import runtime_compute.operations.deduplicate as _impl
from runtime_compute.operations.deduplicate import *  # noqa: F403

sys.modules[__name__] = _impl
