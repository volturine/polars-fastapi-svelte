import sys

import runtime_compute.operations.expression as _impl
from runtime_compute.operations.expression import *  # noqa: F403

sys.modules[__name__] = _impl
