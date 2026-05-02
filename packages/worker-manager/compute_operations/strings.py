import sys

import runtime_compute.operations.strings as _impl
from runtime_compute.operations.strings import *  # noqa: F403

sys.modules[__name__] = _impl
