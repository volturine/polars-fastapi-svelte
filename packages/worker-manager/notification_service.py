import sys

import runtime_compute.notification_service as _impl
from runtime_compute.notification_service import *  # noqa: F403

sys.modules[__name__] = _impl
