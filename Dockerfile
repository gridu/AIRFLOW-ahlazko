FROM puckel/docker-airflow:1.10.6
RUN pip install --user psycopg2-binary
ENV AIRFLOW_HOME=/usr/local/airflow
COPY ./docker_airflow.cfg /usr/local/airflow/airflow.cfg
COPY ./wait-for-it.sh /usr/local/airflow/wait-for-it.sh