import sys

import runtime_compute.ai_service as _impl
from runtime_compute.ai_service import *  # noqa: F403

sys.modules[__name__] = _impl
