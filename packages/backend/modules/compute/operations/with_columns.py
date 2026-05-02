# ruff: noqa: I001
import sys
import compute_operations.with_columns as _impl
from compute_operations.with_columns import *  # noqa: F401,F403
from compute_operations.with_columns import _SAFE_BUILTINS  # noqa: F401

sys.modules[__name__] = _impl
