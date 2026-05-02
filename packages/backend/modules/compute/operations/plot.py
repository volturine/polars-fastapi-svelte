# ruff: noqa: I001
import sys
import compute_operations.plot as _impl
from compute_operations.plot import *  # noqa: F401,F403

sys.modules[__name__] = _impl
