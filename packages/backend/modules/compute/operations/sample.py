# ruff: noqa: I001
import sys
import compute_operations.sample as _impl
from compute_operations.sample import *  # noqa: F401,F403

sys.modules[__name__] = _impl
