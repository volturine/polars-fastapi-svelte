from contracts.compute.base import OperationHandler, OperationParams
from runtime_compute.operations.ai import AIHandler
from runtime_compute.operations.datasource import DatasourceHandler
from runtime_compute.operations.deduplicate import DeduplicateHandler
from runtime_compute.operations.download import DownloadHandler
from runtime_compute.operations.drop import DropHandler
from runtime_compute.operations.explode import ExplodeHandler
from runtime_compute.operations.export import ExportHandler
from runtime_compute.operations.expression import ExpressionHandler
from runtime_compute.operations.fill_null import FillNullHandler
from runtime_compute.operations.filter import FilterHandler
from runtime_compute.operations.groupby import GroupByHandler
from runtime_compute.operations.join import JoinHandler
from runtime_compute.operations.limit import LimitHandler
from runtime_compute.operations.notification import NotificationHandler
from runtime_compute.operations.pivot import PivotHandler
from runtime_compute.operations.plot import ChartHandler
from runtime_compute.operations.rename import RenameHandler
from runtime_compute.operations.sample import SampleHandler
from runtime_compute.operations.select import SelectHandler
from runtime_compute.operations.sort import SortHandler
from runtime_compute.operations.strings import StringTransformHandler
from runtime_compute.operations.timeseries import TimeseriesHandler
from runtime_compute.operations.topk import TopKHandler
from runtime_compute.operations.union import UnionByNameHandler
from runtime_compute.operations.unpivot import UnpivotHandler
from runtime_compute.operations.view import ViewHandler
from runtime_compute.operations.with_columns import WithColumnsHandler

__all__ = [
    'HANDLERS',
    'OperationHandler',
    'OperationParams',
]

HANDLERS: dict[str, OperationHandler] = {
    'datasource': DatasourceHandler(),
    'ai': AIHandler(),
    'deduplicate': DeduplicateHandler(),
    'download': DownloadHandler(),
    'drop': DropHandler(),
    'explode': ExplodeHandler(),
    'export': ExportHandler(),
    'fill_null': FillNullHandler(),
    'filter': FilterHandler(),
    'groupby': GroupByHandler(),
    'join': JoinHandler(),
    'limit': LimitHandler(),
    'notification': NotificationHandler(),
    'pivot': PivotHandler(),
    'rename': RenameHandler(),
    'sample': SampleHandler(),
    'select': SelectHandler(),
    'sort': SortHandler(),
    'string_transform': StringTransformHandler(),
    'timeseries': TimeseriesHandler(),
    'topk': TopKHandler(),
    'union_by_name': UnionByNameHandler(),
    'unpivot': UnpivotHandler(),
    'view': ViewHandler(),
    'with_columns': WithColumnsHandler(),
    'expression': ExpressionHandler(),
    'chart': ChartHandler(),
}
