import sys

import runtime_compute.operations.datasource as _impl
from runtime_compute.operations.datasource import *  # noqa: F403

_analysis_stack_var = _impl._analysis_stack_var
_assert_select_only = _impl._assert_select_only

sys.modules[__name__] = _impl
