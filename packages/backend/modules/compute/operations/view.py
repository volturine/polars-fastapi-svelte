import sys

import runtime_compute.operations.view as _impl
from runtime_compute.operations.view import *  # noqa: F403

sys.modules[__name__] = _impl
