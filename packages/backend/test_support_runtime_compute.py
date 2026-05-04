from __future__ import annotations

import importlib
from typing import Any


def preview_step(**kwargs: Any):
    return importlib.import_module('compute_service').preview_step(**kwargs)


def get_step_schema(**kwargs: Any):
    return importlib.import_module('compute_service').get_step_schema(**kwargs)


def get_step_row_count(**kwargs: Any):
    return importlib.import_module('compute_service').get_step_row_count(**kwargs)


def download_step(**kwargs: Any):
    return importlib.import_module('compute_service').download_step(**kwargs)


def export_data(**kwargs: Any):
    return importlib.import_module('compute_service').export_data(**kwargs)
