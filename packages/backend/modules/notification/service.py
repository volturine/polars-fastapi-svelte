# ruff: noqa: I001
import sys
import core.notification_service as _impl
from core.notification_service import *  # noqa: F401,F403

sys.modules[__name__] = _impl
