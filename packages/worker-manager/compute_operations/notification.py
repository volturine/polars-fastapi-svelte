import sys

import runtime_compute.operations.notification as _impl
from runtime_compute.operations.notification import *  # noqa: F403

_build_message = _impl._build_message

sys.modules[__name__] = _impl
