# ruff: noqa: I001
import sys
import compute_operations.notification as _impl
from compute_operations.notification import *  # noqa: F401,F403
from compute_operations.notification import _build_message  # noqa: F401

sys.modules[__name__] = _impl
