import sys

import runtime_compute.healthcheck_service as _impl
from runtime_compute.healthcheck_service import *  # noqa: F403

sys.modules[__name__] = _impl
