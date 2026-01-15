import multiprocessing as mp
import uuid
from datetime import datetime, timezone
from typing import Any

import polars as pl

from modules.compute.schemas import JobStatus


class PolarsComputeEngine:
    def __init__(self, analysis_id: str):
        self.analysis_id = analysis_id
        self.process: mp.Process | None = None
        self.command_queue: mp.Queue = mp.Queue()
        self.result_queue: mp.Queue = mp.Queue()
        self.is_running = False
        self.current_job_id: str | None = None

    def start(self) -> None:
        """Start the compute subprocess"""
        if self.is_running:
            return

        self.process = mp.Process(
            target=self._run_compute,
            args=(self.command_queue, self.result_queue),
        )
        self.process.start()
        self.is_running = True

    def execute(self, datasource_config: dict, pipeline_steps: list[dict], timeout: int = 300) -> str:
        """Execute a Polars pipeline in the subprocess"""
        job_id = str(uuid.uuid4())
        self.current_job_id = job_id

        if not self.is_running:
            self.start()

        command = {
            'type': 'execute',
            'job_id': job_id,
            'datasource_config': datasource_config,
            'pipeline_steps': pipeline_steps,
            'timeout': timeout,
        }

        self.command_queue.put(command)
        return job_id

    def get_result(self, timeout: float = 1.0) -> dict | None:
        """Get result from result queue (non-blocking)"""
        try:
            return self.result_queue.get(timeout=timeout)
        except:
            return None

    def shutdown(self) -> None:
        """Shutdown the compute subprocess"""
        if not self.is_running:
            return

        self.command_queue.put({'type': 'shutdown'})

        if self.process and self.process.is_alive():
            self.process.join(timeout=5)
            if self.process.is_alive():
                self.process.terminate()
                self.process.join(timeout=2)
            if self.process.is_alive():
                self.process.kill()

        self.is_running = False
        self.process = None

    @staticmethod
    def _run_compute(command_queue: mp.Queue, result_queue: mp.Queue) -> None:
        """Main compute loop running in subprocess"""
        while True:
            try:
                command = command_queue.get()

                if command['type'] == 'shutdown':
                    break

                if command['type'] == 'execute':
                    job_id = command['job_id']
                    datasource_config = command['datasource_config']
                    pipeline_steps = command['pipeline_steps']

                    result_queue.put(
                        {
                            'job_id': job_id,
                            'status': JobStatus.RUNNING,
                            'progress': 0.0,
                            'current_step': 'Loading data',
                            'error': None,
                        }
                    )

                    try:
                        result_data = PolarsComputeEngine._execute_pipeline(
                            datasource_config,
                            pipeline_steps,
                            job_id,
                            result_queue,
                        )

                        result_queue.put(
                            {
                                'job_id': job_id,
                                'status': JobStatus.COMPLETED,
                                'progress': 1.0,
                                'current_step': None,
                                'data': result_data,
                                'error': None,
                            }
                        )

                    except Exception as e:
                        result_queue.put(
                            {
                                'job_id': job_id,
                                'status': JobStatus.FAILED,
                                'progress': 0.0,
                                'current_step': None,
                                'error': str(e),
                            }
                        )

            except Exception as e:
                result_queue.put(
                    {
                        'job_id': 'unknown',
                        'status': JobStatus.FAILED,
                        'progress': 0.0,
                        'current_step': None,
                        'error': f'Compute loop error: {str(e)}',
                    }
                )

    @staticmethod
    def _execute_pipeline(
        datasource_config: dict,
        pipeline_steps: list[dict],
        job_id: str,
        result_queue: mp.Queue,
    ) -> dict:
        """Execute the Polars transformation pipeline"""
        df = PolarsComputeEngine._load_datasource(datasource_config)

        total_steps = len(pipeline_steps)

        for idx, step in enumerate(pipeline_steps):
            progress = (idx + 1) / total_steps
            step_name = step.get('name', f'Step {idx + 1}')

            result_queue.put(
                {
                    'job_id': job_id,
                    'status': JobStatus.RUNNING,
                    'progress': progress,
                    'current_step': step_name,
                    'error': None,
                }
            )

            df = PolarsComputeEngine._apply_step(df, step)

        output = {
            'schema': {col: str(dtype) for col, dtype in df.schema.items()},
            'row_count': len(df),
            'sample_data': df.head(100).to_dicts(),
        }

        return output

    @staticmethod
    def _load_datasource(config: dict) -> pl.DataFrame:
        """Load data from datasource configuration"""
        source_type = config.get('source_type', 'file')

        if source_type == 'file':
            file_path = config['file_path']
            file_type = config['file_type']

            if file_type == 'csv':
                return pl.read_csv(file_path)
            elif file_type == 'parquet':
                return pl.read_parquet(file_path)
            elif file_type == 'json':
                return pl.read_ndjson(file_path)
            else:
                raise ValueError(f'Unsupported file type: {file_type}')

        elif source_type == 'database':
            connection_string = config['connection_string']
            query = config['query']
            return pl.read_database(query, connection_string)

        else:
            raise ValueError(f'Unsupported source type: {source_type}')

    @staticmethod
    def _apply_step(df: pl.DataFrame, step: dict) -> pl.DataFrame:
        """Apply a single transformation step to the DataFrame"""
        operation = step.get('operation')
        params = step.get('params', {})

        if operation == 'filter':
            expr = params.get('expression')
            return df.filter(pl.col(expr['column']) == expr['value'])

        elif operation == 'select':
            columns = params.get('columns', [])
            return df.select(columns)

        elif operation == 'groupby':
            group_cols = params.get('group_by', [])
            agg_cols = params.get('aggregations', [])

            agg_exprs = []
            for agg in agg_cols:
                col = agg['column']
                func = agg['function']

                if func == 'sum':
                    agg_exprs.append(pl.col(col).sum().alias(f'{col}_sum'))
                elif func == 'mean':
                    agg_exprs.append(pl.col(col).mean().alias(f'{col}_mean'))
                elif func == 'count':
                    agg_exprs.append(pl.col(col).count().alias(f'{col}_count'))
                elif func == 'min':
                    agg_exprs.append(pl.col(col).min().alias(f'{col}_min'))
                elif func == 'max':
                    agg_exprs.append(pl.col(col).max().alias(f'{col}_max'))

            return df.group_by(group_cols).agg(agg_exprs)

        elif operation == 'sort':
            columns = params.get('columns', [])
            descending = params.get('descending', False)
            return df.sort(columns, descending=descending)

        elif operation == 'rename':
            mapping = params.get('mapping', {})
            return df.rename(mapping)

        elif operation == 'with_columns':
            expressions = params.get('expressions', [])
            new_cols = []

            for expr in expressions:
                col_name = expr['name']
                expr_type = expr['type']

                if expr_type == 'literal':
                    new_cols.append(pl.lit(expr['value']).alias(col_name))
                elif expr_type == 'column':
                    new_cols.append(pl.col(expr['column']).alias(col_name))

            return df.with_columns(new_cols)

        elif operation == 'drop':
            columns = params.get('columns', [])
            return df.drop(columns)

        else:
            raise ValueError(f'Unsupported operation: {operation}')
