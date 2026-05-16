from contracts.enums import DataForgeStrEnum


class DataSourceCategory(DataForgeStrEnum):
    FILE = 'file'
    DATABASE = 'database'
    ANALYSIS = 'analysis'

    @property
    def is_file_based(self) -> bool:
        return self == DataSourceCategory.FILE


class DataSourceType(DataForgeStrEnum):
    FILE = 'file'
    DATABASE = 'database'
    ICEBERG = 'iceberg'
    ANALYSIS = 'analysis'

    @property
    def category(self) -> DataSourceCategory:
        if self in {DataSourceType.FILE, DataSourceType.ICEBERG}:
            return DataSourceCategory.FILE
        if self == DataSourceType.DATABASE:
            return DataSourceCategory.DATABASE
        return DataSourceCategory.ANALYSIS

    @property
    def is_file_based(self) -> bool:
        return self.category.is_file_based
