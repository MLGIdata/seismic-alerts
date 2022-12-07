'''
Script de airflow carga continua de datos sísmicos de USA desde USGS. A partir de la última hora de carga
se cargan los datos nuevos hasta el momento en que se corre el script.
'''

from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python_operator import PythonOperator
import boto3
from UShourly import main,pushS3

default_args={
    'owner': 'Airflow',
    'start_date': datetime(2022,11,20),
    'retries': 3,
    'retry_delay': timedelta(seconds=3)
}

with DAG (
    "US_Hourly_Upload",
    default_args = default_args,
    schedule_interval = '@daily',
    catchup=False
    ) as dag:

    extract_and_transform = PythonOperator(
        task_id = "extract_and_transform",
        python_callable = main
    )

    load = PythonOperator(
        task_id = "load",
        python_callable = pushS3,
        op_kwargs = {
            'path': 'dags/data/usa_usgs.csv',
            'id': 'USAdata'
        }
    )

    extract_and_transform >> load 