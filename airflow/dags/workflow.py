from airflow import DAG
from datetime import datetime,timedelta
from airflow.models import Connection
from airflow import models, settings
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.postgres_operator import PostgresOperator
import sys
import os
import pandas as pd
import json

print(os.path.abspath("working.............................."))
sys.path.append(os.path.abspath("includes/python"))

from ingest_global import Ingest

ingest_jsons = Ingest()

DBT_PROJECT_DIR = "~/dbt_"
DBT_PROFILE_DIR = "~/dbt_/.dbt"

def json_extract(**context):
    
    json_data =ingest_jsons.load_json("data/global_design_data.json")
    flattened_json = ingest_jsons.flatten_json(json_data)
    final_data = ingest_jsons.restructure(flattened_json)
    path = "data/global_design_data.csv"
    final_data.to_csv(path, index=False)
    print("successful")
 
def set_connection(**config):
    conn = Connection(
        conn_id="2data_lake",
        conn_type="Postgres",
        host="postgres",
        login="data_lake",
        password="data_lake",
        schema="data_lake",
        port=5432
    )
    conn2 = Connection(
        conn_id="3staging",
        conn_type="Postgres",
        host="postgres",
        login="staging",
        password="staging",
        schema="staging",
        port=5432
    )
    conn3 = Connection(
        conn_id="2warehouse",
        conn_type="Postgres",
        host="postgres",
        login="warehouse",
        password="warehouse",
        schema="warehouse",
        port=5432
    )
    session = settings.Session()
    session.add(conn)
    session.add(conn2)
    session.add(conn3)
    session.commit()
    session.close()


    
default_args = {"owner":"airflow","start_date":datetime(2021,3,7)}
with DAG(dag_id="workflow",template_searchpath='includes/sql/',default_args=default_args,schedule_interval='@daily', catchup=False) as dag:
    
    task = PythonOperator(
                    dag = dag,
                    task_id = 'set-connections',
                    python_callable = set_connection
                )
    run_json_extract= PythonOperator(
                    task_id = "run_json_extract",
                    python_callable = json_extract,
                    provide_context=True
                )
    run_ingestion= PostgresOperator(
                    task_id="run_ingestion",
                    postgres_conn_id="2data_lake",
                    sql="ingestion.sql",
                )
    run_extraction= PostgresOperator(
                    task_id="run_extraction",
                    postgres_conn_id="3staging",
                    sql="extraction.sql",
                )
    run_preprocessing= PostgresOperator(
                    task_id="run_preprocessing",
                    postgres_conn_id="3staging",
                    sql="clean_data.sql",
                )
    run_transformation = BashOperator(
                    task_id="run_transformation",
                    bash_command=f"cd ~/dbt_ && ~/.local/bin/dbt run --profiles-dir {DBT_PROFILE_DIR}",
                ),
    run_tests = BashOperator(
                    task_id="run_tests",
                    bash_command=f"cd ~/dbt_ && ~/.local/bin/dbt test --profiles-dir {DBT_PROFILE_DIR}",
                )
    run_loading= PostgresOperator(
                    task_id="run_loading",
                    postgres_conn_id="2warehouse",
                    sql="loading.sql",
                )
    dbt_doc = BashOperator(
                    task_id="dbt_doc",
                    bash_command=f"cd ~/dbt_ && ~/.local/bin/dbt docs generate --profiles-dir {DBT_PROFILE_DIR} && ~/.local/bin/dbt docs serve --port 7211 --profiles-dir {DBT_PROFILE_DIR}",
                )

task >> run_json_extract >> run_ingestion >> run_extraction >> run_preprocessing >> run_transformation >> run_tests >> run_loading
run_transformation >> dbt_doc