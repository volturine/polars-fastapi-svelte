import sys

import runtime_compute.utils as _impl
from runtime_compute.utils import *  # noqa: F403

sys.modules[__name__] = _impl
