# ruff: noqa: I001
import sys
import iceberg_reader as _impl
from iceberg_reader import *  # noqa: F401,F403

sys.modules[__name__] = _impl
