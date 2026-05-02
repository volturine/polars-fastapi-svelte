# ruff: noqa: I001
import sys
import compute_operations as _impl
from compute_operations import *  # noqa: F401,F403

sys.modules[__name__] = _impl
