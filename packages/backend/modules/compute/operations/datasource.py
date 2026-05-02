# ruff: noqa: I001
import sys
import compute_operations.datasource as _impl
from compute_operations.datasource import *  # noqa: F401,F403
from compute_operations.datasource import _analysis_stack_var, _assert_select_only  # noqa: F401

sys.modules[__name__] = _impl
