from datetime import datetime
from airflow import DAG

default_args = {
  'owner': 'Ann',
  'start_date': datetime(2020, 3, 26)
}
dag = DAG('gridu_dag', default_args=default_args, schedule_interval='@once')