# ruff: noqa: I001
import sys
import compute_operations.strings as _impl
from compute_operations.strings import *  # noqa: F401,F403

sys.modules[__name__] = _impl
