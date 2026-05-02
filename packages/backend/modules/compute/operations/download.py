import sys

import runtime_compute.operations.download as _impl
from runtime_compute.operations.download import *  # noqa: F403

sys.modules[__name__] = _impl
