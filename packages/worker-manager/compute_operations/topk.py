import sys

import runtime_compute.operations.topk as _impl
from runtime_compute.operations.topk import *  # noqa: F403

sys.modules[__name__] = _impl
