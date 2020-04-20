from airflow import DAG
from datetime import datetime
from airflow.contrib.sensors.file_sensor import FileSensor
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.subdag_operator import SubDagOperator
from airflow.sensors.external_task_sensor import ExternalTaskSensor
from airflow.operators.python_operator import PythonOperator
import os
import logging


path = os.path.abspath('my_dir/forum_users.tsv')
base_path = os.path.abspath('my_dir/')
# my_path = Variable.get('variable_for_ path')
PARENT_DAG_NAME = "my_dag"
CHILD_DAG_NAME = "child_dag"


def print_results(**context):
    task_instance = context['task_instance']
    value = task_instance.xcom_pull(task_ids="query", dag_id="log_info")
    logging.info("%s", value)
    logging.info("%s", context)


def sub_dag(parent_dag_name, child_dag_name, start_date, ex_data):
    sub_dag = DAG('%s.%s' % (parent_dag_name, child_dag_name),schedule_interval='@once', max_active_runs=1,
              start_date=start_date,)
    with sub_dag:
        ext_sens = ExternalTaskSensor(task_id="sensor_triggered_dag", external_dag_id="my_dag",
                                      external_task_id='my_run_op')
        create_file = BashOperator(task_id="create_file",
                                   bash_command='touch {{ params.path }}/finished_{{ ts_nodash }}',
                                   dag=sub_dag, params={"path": base_path})
        print_res = PythonOperator(task_id="print_result", provide_context=True,
                                   python_callable=print_results,
                                   dag=sub_dag)
        t3 = BashOperator(task_id="delete", bash_command='rm {}'.format(path), dag=sub_dag)
        ext_sens >>  print_res >> t3 >> create_file
    return sub_dag


with DAG("my_dag", start_date=datetime(2020, 3, 26), schedule_interval='@once', max_active_runs=1) as main_dag:
    t1 = FileSensor(task_id="my_sensor", poke_interval=60*2, filepath=path, dag=main_dag)
    t2 = TriggerDagRunOperator(task_id="my_run_op", trigger_dag_id="my_dag",dag=main_dag)
    sub_dag_task = SubDagOperator(task_id=CHILD_DAG_NAME,
                                  subdag=sub_dag(PARENT_DAG_NAME, CHILD_DAG_NAME, main_dag.start_date,
                                  "{{ ds }}"), dag=main_dag)
    # t3 = BashOperator(task_id="delete", bash_command='rm {}'.format(path), dag=dag)
    t1 >> t2 >> sub_dag_task

