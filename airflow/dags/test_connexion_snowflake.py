"""DAG minimal pour valider la connexion Snowflake (jour 3).

À lancer avec le bouton Trigger (schedule=None).
"""

import pendulum
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.sdk import dag, task

CONN_ID = "snowflake_nyc_taxi"


@dag(
    dag_id="test_connexion_snowflake",
    schedule=None,
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    tags=["test", "snowflake"],
)
def test_connexion_snowflake():
    @task
    def qui_suis_je():
        ligne = SnowflakeHook(snowflake_conn_id=CONN_ID).get_first(
            "SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE()"
        )
        print(ligne)
        return ligne

    qui_suis_je()


test_connexion_snowflake()
