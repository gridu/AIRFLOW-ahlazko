from airflow.models.baseoperator import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.hooks.postgres_hook import PostgresHook
from airflow.plugins_manager import AirflowPlugin

import logging


logger = logging.getLogger(__name__)


class PostgreSQLCountRows(BaseOperator):
    @apply_defaults
    def __init__(self, table_name, *args, **kwargs):
        self.table_name = table_name
        self.hook = PostgresHook(postgres_conn_id="connection1")
        super(PostgreSQLCountRows, self).__init__(*args, **kwargs)

    def execute(self, context):
        query_result = self.hook.get_first(sql="SELECT COUNT(*) FROM {};".format(self.table_name))
        logger.info("Count: {}".format(query_result[0]))
        return query_result[0]


class PostgreSQLCustomOperatorsPlugin(AirflowPlugin):
    name = "postgres_custom"
    operators = [PostgreSQLCountRows]
