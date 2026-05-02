# ruff: noqa: I001
import sys
import compute_manager as _impl
from compute_manager import *  # noqa: F401,F403

sys.modules[__name__] = _impl
