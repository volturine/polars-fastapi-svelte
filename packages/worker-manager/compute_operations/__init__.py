from contracts.compute.base import OperationHandler, OperationParams

from compute_operations.ai import AIHandler
from compute_operations.datasource import DatasourceHandler
from compute_operations.deduplicate import DeduplicateHandler
from compute_operations.download import DownloadHandler
from compute_operations.drop import DropHandler
from compute_operations.explode import ExplodeHandler
from compute_operations.export import ExportHandler
from compute_operations.expression import ExpressionHandler
from compute_operations.fill_null import FillNullHandler
from compute_operations.filter import FilterHandler
from compute_operations.groupby import GroupByHandler
from compute_operations.join import JoinHandler
from compute_operations.limit import LimitHandler
from compute_operations.notification import NotificationHandler
from compute_operations.pivot import PivotHandler
from compute_operations.plot import ChartHandler
from compute_operations.rename import RenameHandler
from compute_operations.sample import SampleHandler
from compute_operations.select import SelectHandler
from compute_operations.sort import SortHandler
from compute_operations.strings import StringTransformHandler
from compute_operations.timeseries import TimeseriesHandler
from compute_operations.topk import TopKHandler
from compute_operations.union import UnionByNameHandler
from compute_operations.unpivot import UnpivotHandler
from compute_operations.view import ViewHandler
from compute_operations.with_columns import WithColumnsHandler

__all__ = [
    "HANDLERS",
    "OperationHandler",
    "OperationParams",
]

HANDLERS: dict[str, OperationHandler] = {
    "datasource": DatasourceHandler(),
    "ai": AIHandler(),
    "deduplicate": DeduplicateHandler(),
    "download": DownloadHandler(),
    "drop": DropHandler(),
    "explode": ExplodeHandler(),
    "export": ExportHandler(),
    "fill_null": FillNullHandler(),
    "filter": FilterHandler(),
    "groupby": GroupByHandler(),
    "join": JoinHandler(),
    "limit": LimitHandler(),
    "notification": NotificationHandler(),
    "pivot": PivotHandler(),
    "rename": RenameHandler(),
    "sample": SampleHandler(),
    "select": SelectHandler(),
    "sort": SortHandler(),
    "string_transform": StringTransformHandler(),
    "timeseries": TimeseriesHandler(),
    "topk": TopKHandler(),
    "union_by_name": UnionByNameHandler(),
    "unpivot": UnpivotHandler(),
    "view": ViewHandler(),
    "with_columns": WithColumnsHandler(),
    "expression": ExpressionHandler(),
    "chart": ChartHandler(),
}
