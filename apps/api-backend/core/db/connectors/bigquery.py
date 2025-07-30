"""BigQuery database connector implementation."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

from google.cloud import bigquery
from google.cloud.bigquery import Client, QueryJob
from google.oauth2 import service_account

from models import DatabaseType, TableSchema, ColumnSchema
from .base import BaseDatabaseConnector, ConnectionConfig

logger = logging.getLogger(__name__)


class BigQueryConnector(BaseDatabaseConnector):
    """BigQuery database connector with connection pooling."""

    def __init__(self, config: ConnectionConfig):
        if config.database_type != DatabaseType.BIGQUERY:
            raise ValueError("Config must be for BigQuery database")
        super().__init__(config)
        self._client: Optional[Client] = None
        self._executor = ThreadPoolExecutor(max_workers=config.max_connections)

    async def _create_pool(self) -> Client:
        """Create BigQuery client."""
        try:
            # BigQuery connection parameters
            project_id = self.config.options.get("project_id", self.config.database)

            # Authentication options
            if "credentials_path" in self.config.options:
                # Service account key file
                credentials = service_account.Credentials.from_service_account_file(
                    self.config.options["credentials_path"]
                )
                client = bigquery.Client(project=project_id, credentials=credentials)
            elif "credentials_json" in self.config.options:
                # Service account key as JSON
                import json

                credentials_info = json.loads(self.config.options["credentials_json"])
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_info
                )
                client = bigquery.Client(project=project_id, credentials=credentials)
            else:
                # Use default credentials (ADC)
                client = bigquery.Client(project=project_id)

            # Test the connection
            await asyncio.get_event_loop().run_in_executor(
                self._executor, lambda: list(client.list_datasets(max_results=1))
            )

            logger.info(f"BigQuery client created for project: {project_id}")
            return client

        except Exception as e:
            logger.error(f"Failed to create BigQuery client: {e}")
            raise

    async def _close_pool(self) -> None:
        """Close BigQuery client."""
        if self._client:
            # BigQuery client doesn't need explicit closing
            self._client = None
            logger.info("BigQuery client closed")

    @asynccontextmanager
    async def _get_connection(self) -> AsyncGenerator[Client, None]:
        """Get BigQuery client."""
        if not self._client:
            raise RuntimeError("BigQuery client not initialized")

        try:
            yield self._client
        except Exception as e:
            logger.error(f"BigQuery client error: {e}")
            raise

    async def _execute_query(
        self, client: Client, sql: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute query on BigQuery."""
        try:

            def _execute():
                job_config = bigquery.QueryJobConfig()

                if params:
                    # Convert parameters to BigQuery format
                    query_parameters = []
                    formatted_sql = sql

                    for key, value in params.items():
                        # Replace :param with @param for BigQuery
                        formatted_sql = formatted_sql.replace(f":{key}", f"@{key}")

                        # Determine parameter type
                        if isinstance(value, str):
                            param_type = "STRING"
                        elif isinstance(value, int):
                            param_type = "INT64"
                        elif isinstance(value, float):
                            param_type = "FLOAT64"
                        elif isinstance(value, bool):
                            param_type = "BOOL"
                        else:
                            param_type = "STRING"
                            value = str(value)

                        query_parameters.append(
                            bigquery.ScalarQueryParameter(key, param_type, value)
                        )

                    job_config.query_parameters = query_parameters
                    sql = formatted_sql

                # Execute query
                query_job: QueryJob = client.query(sql, job_config=job_config)
                results = query_job.result()

                # Convert to list of dictionaries
                return [dict(row) for row in results]

            result = await asyncio.get_event_loop().run_in_executor(
                self._executor, _execute
            )

            return result or []

        except Exception as e:
            logger.error(f"BigQuery query execution failed: {e}")
            raise

    async def _explain_query(self, client: Client, sql: str) -> str:
        """Get BigQuery query execution plan."""
        try:

            def _explain():
                # BigQuery doesn't have a traditional EXPLAIN, but we can get job statistics
                job_config = bigquery.QueryJobConfig(
                    dry_run=True, use_query_cache=False
                )
                query_job: QueryJob = client.query(sql, job_config=job_config)

                # Get query statistics
                stats = query_job.to_api_repr().get("statistics", {})
                query_stats = stats.get("query", {})

                output = []

                if "totalBytesProcessed" in query_stats:
                    bytes_processed = int(query_stats["totalBytesProcessed"])
                    output.append(f"Total Bytes Processed: {bytes_processed:,}")

                if "totalSlotMs" in query_stats:
                    slot_ms = int(query_stats["totalSlotMs"])
                    output.append(f"Total Slot Time: {slot_ms:,} ms")

                if "cacheHit" in query_stats:
                    cache_hit = query_stats["cacheHit"]
                    output.append(f"Cache Hit: {cache_hit}")

                if "referencedTables" in query_stats:
                    tables = query_stats["referencedTables"]
                    table_names = []
                    for table in tables:
                        project = table.get("projectId", "")
                        dataset = table.get("datasetId", "")
                        table_name = table.get("tableId", "")
                        table_names.append(f"{project}.{dataset}.{table_name}")
                    output.append(f"Referenced Tables: {', '.join(table_names)}")

                if "queryPlan" in query_stats:
                    plan_stages = query_stats["queryPlan"]
                    output.append(f"Query Plan Stages: {len(plan_stages)}")

                    for i, stage in enumerate(plan_stages):
                        stage_name = stage.get("name", f"Stage {i}")
                        output.append(
                            f"  {stage_name}: {stage.get('status', 'Unknown')}"
                        )

                return (
                    "\n".join(output)
                    if output
                    else "No execution plan information available"
                )

            return await asyncio.get_event_loop().run_in_executor(
                self._executor, _explain
            )

        except Exception as e:
            logger.error(f"Failed to get BigQuery execution plan: {e}")
            raise

    async def _get_table_metadata(self, client: Client, table_name: str) -> TableSchema:
        """Get BigQuery table metadata."""
        try:

            def _get_metadata():
                # Parse table name (could be project.dataset.table or dataset.table)
                parts = table_name.split(".")
                if len(parts) == 3:
                    project_id, dataset_id, table_id = parts
                elif len(parts) == 2:
                    project_id = client.project
                    dataset_id, table_id = parts
                else:
                    # Assume default dataset from options
                    project_id = client.project
                    dataset_id = self.config.options.get("dataset_id", "")
                    table_id = table_name

                if not dataset_id:
                    raise ValueError(
                        "Dataset ID not specified and no default dataset configured"
                    )

                # Get table reference
                table_ref = client.dataset(dataset_id, project=project_id).table(
                    table_id
                )
                table = client.get_table(table_ref)

                # Get column information
                columns = []
                for field in table.schema:
                    # Get sample values for low-cardinality columns
                    sample_values = (
                        []
                    )  # BigQuery sample values would require additional queries

                    column = ColumnSchema(
                        name=field.name,
                        data_type=field.field_type.lower(),
                        description=field.description,
                        sample_values=sample_values,
                        is_nullable=field.mode != "REQUIRED",
                        is_primary_key=False,  # BigQuery doesn't have traditional primary keys
                        is_foreign_key=False,
                    )
                    columns.append(column)

                return table, columns

            table, columns = await asyncio.get_event_loop().run_in_executor(
                self._executor, _get_metadata
            )

            return TableSchema(
                name=table_name,
                database_id=f"{table.project}.{table.dataset_id}",
                columns=columns,
                description=table.description,
                row_count=table.num_rows,
            )

        except Exception as e:
            logger.error(f"Failed to get BigQuery table metadata for {table_name}: {e}")
            raise

    async def _get_sample_values(
        self, client: Client, table_name: str, column_name: str, limit: int = 10
    ) -> List[Any]:
        """Get sample values for a column."""
        try:

            def _get_samples():
                # Check if column has low cardinality (< 100 distinct values)
                distinct_query = f"""
                    SELECT COUNT(DISTINCT `{column_name}`) as distinct_count
                    FROM `{table_name}`
                """

                job = client.query(distinct_query)
                results = list(job.result())
                distinct_count = results[0]["distinct_count"] if results else 0

                if distinct_count and distinct_count < 100:
                    # Get sample values for low-cardinality columns
                    sample_query = f"""
                        SELECT DISTINCT `{column_name}`
                        FROM `{table_name}`
                        WHERE `{column_name}` IS NOT NULL
                        ORDER BY `{column_name}`
                        LIMIT {limit}
                    """

                    job = client.query(sample_query)
                    results = list(job.result())
                    return [row[column_name] for row in results]

                return []

            return await asyncio.get_event_loop().run_in_executor(
                self._executor, _get_samples
            )

        except Exception as e:
            logger.warning(
                f"Failed to get sample values for {table_name}.{column_name}: {e}"
            )
            return []

    async def _list_tables(self, client: Client) -> List[str]:
        """List all BigQuery tables."""
        try:

            def _list():
                dataset_id = self.config.options.get("dataset_id")
                if not dataset_id:
                    # List all datasets and their tables
                    all_tables = []
                    for dataset in client.list_datasets():
                        dataset_ref = client.dataset(dataset.dataset_id)
                        for table in client.list_tables(dataset_ref):
                            all_tables.append(f"{dataset.dataset_id}.{table.table_id}")
                    return sorted(all_tables)
                else:
                    # List tables in specific dataset
                    dataset_ref = client.dataset(dataset_id)
                    tables = []
                    for table in client.list_tables(dataset_ref):
                        tables.append(table.table_id)
                    return sorted(tables)

            return await asyncio.get_event_loop().run_in_executor(self._executor, _list)

        except Exception as e:
            logger.error(f"Failed to list BigQuery tables: {e}")
            raise

    async def _health_check_query(self, client: Client) -> None:
        """Execute BigQuery health check query."""

        def _health_check():
            job = client.query("SELECT 1 as health_check")
            list(job.result())  # Consume the results

        await asyncio.get_event_loop().run_in_executor(self._executor, _health_check)
