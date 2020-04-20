from airflow import DAG
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.bash_operator import BashOperator
from airflow.hooks.postgres_hook import PostgresHook
from airflow.operators.postgres_operator import PostgresOperator
from random import randint
from datetime import datetime
from airflow.operators.postgres_custom import PostgreSQLCountRows


config = {
   'log_info': {"start_date": datetime(2020, 3, 26), "table_name": "print_log_info"},
   'insert_dag': {"start_date": datetime(2020, 3, 26), "table_name": "dags_inform"},
   'query_dag': {"start_date": datetime(2020, 3, 26), "table_name": "query_the_table"}}

schema = 'public'
table_name = 'about_dag'


def print_log(dag_name, **kwargs):
    return "{dag_id} start processing tables in database: {database}".format(dag_id=dag_name,
                                                                             database=config[dag_name]['table_name'])


def check_table_exist(sql_to_check_table):
    hook = PostgresHook(postgres_conn_id='connection1')
    query = hook.get_first(sql=sql_to_check_table.format(schema, table_name))
    if query:
        return "skip_table_creation"
    else:
        return "create_table"


def save_xcom(sql_to_count, **context):
    hook = PostgresHook(postgres_conn_id="connection1")
    query = hook.get_first(sql=sql_to_count)
    return query[0]


for name, conf in config.items():
    with DAG(name, default_args=conf, schedule_interval=None) as dag:
        print_process_start = PythonOperator(
            task_id="print_process_start",
            provide_context=True,
            python_callable=print_log,
            op_args=(name,),
            dag=dag
        )

        insert_row = PostgresOperator(
            task_id="insert_row",
            sql="INSERT INTO about_dag (custom_id, user_name, timestamp) VALUES (%s, "
                "'{{ task_instance.xcom_pull(task_ids='exec_bash_to_get_user', key='return_value') }}', %s);",
            parameters=(randint(1, 100), datetime.now()),
            postgres_conn_id='connection1',
            autocommit=True,
            dag=dag,
            trigger_rule='all_done')

        query_table = PostgreSQLCountRows(
            task_id="query_table",
            dag=dag,
            table_name="about_dag",
            provide_context=True
        )
        check_table_ex = BranchPythonOperator(
            task_id='check_table_exist',
            python_callable=check_table_exist,
            op_args=["SELECT * FROM information_schema.tables "
                     "WHERE table_schema = '{}' "
                     "AND table_name = '{}';"],
            # provide_context=True,
            dag=dag)
        exec_bash_to_get_user = BashOperator(
            task_id='exec_bash_to_get_user',
            xcom_push=True,
            bash_command='echo $(whoami)')
        create_table = PostgresOperator(
            task_id='create_table',
            autocommit=True,
            sql=["CREATE TABLE about_dag (custom_id integer NOT NULL, "
                 "user_name VARCHAR (50) NOT NULL, "
                 "timestamp TIMESTAMP NOT NULL);"],
            postgres_conn_id='connection1',
            dag=dag)
        skip_table_creation = DummyOperator(task_id='skip_table_creation', dag=dag)
        print_process_start >> exec_bash_to_get_user\
        >> check_table_ex >> [create_table, skip_table_creation] >> insert_row >> query_table
        globals()[name] = dag
