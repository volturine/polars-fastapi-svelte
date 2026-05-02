# ruff: noqa: I001
import sys
import compute_operations.drop as _impl
from compute_operations.drop import *  # noqa: F401,F403

sys.modules[__name__] = _impl
