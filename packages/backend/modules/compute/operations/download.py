# ruff: noqa: I001
import sys
import compute_operations.download as _impl
from compute_operations.download import *  # noqa: F401,F403

sys.modules[__name__] = _impl
