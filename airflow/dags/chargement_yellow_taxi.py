"""Chargement + transformations Yellow Taxi (jours 3 et 4).

Ne pas utiliser Trigger : le fichier du mois courant n'existe pas.
Après ajout de tâches, Clear les runs déjà terminés pour les rejouer.
"""

from pathlib import Path

import pendulum
import requests
from airflow.providers.common.sql.operators.sql import SQLCheckOperator, SQLExecuteQueryOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.sdk import TaskGroup, dag, task, get_current_context

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
STAGE = "NYC_TAXI.RAW.NYC_TAXI_STAGE"
TABLE = "NYC_TAXI.RAW.YELLOW_TRIPDATA"
FORMAT_FICHIER = "NYC_TAXI.RAW.PARQUET_FF"
CONN_ID = "snowflake_nyc_taxi"


def sql_task(task_id: str, sql: str, *, split: bool = False) -> SQLExecuteQueryOperator:
    """Exécute un fichier SQL Snowflake."""
    return SQLExecuteQueryOperator(
        task_id=task_id,
        conn_id=CONN_ID,
        sql=sql,
        split_statements=split,
    )


def check_task(task_id: str, sql: str) -> SQLCheckOperator:
    """Contrôle qualité : une ligne, valeurs vraies, sinon échec (sans retry)."""
    return SQLCheckOperator(
        task_id=task_id,
        conn_id=CONN_ID,
        sql=sql,
        retries=0,
    )


@dag(
    dag_id="chargement_yellow_taxi",
    schedule="@monthly",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    end_date=pendulum.datetime(2025, 3, 1, tz="UTC"),
    catchup=True,
    max_active_runs=1,
    template_searchpath="/usr/local/airflow/include/sql",
    params={
        "max_trip_distance_miles": 100,
        "max_trip_duration_min": 180,
        "start_month": "2025-01-01",
        "end_month": "2025-04-01",
        "max_pct_rejetes": 15,
    },
    default_args={"retries": 2, "retry_delay": pendulum.duration(minutes=5)},
    tags=["ingestion", "nyc_taxi"],
)
def chargement_yellow_taxi():

    @task
    def nom_du_fichier() -> str:
        """Nom du Parquet déduit du mois de l'exécution (pas d'aujourd'hui)."""
        ctx = get_current_context()
        mois = ctx["data_interval_start"].strftime("%Y-%m")
        return f"yellow_tripdata_{mois}.parquet"

    @task
    def verifier_disponibilite(fichier: str) -> str:
        """Échoue si le mois n'est pas encore publié sur le CDN TLC."""
        url = f"{BASE_URL}/{fichier}"
        requests.head(url, timeout=30).raise_for_status()
        return url

    @task
    def telecharger_et_deposer(url: str) -> str:
        """Télécharge le fichier puis le dépose sur le stage (même tâche)."""
        destination = Path("/tmp") / url.rsplit("/", 1)[-1]
        try:
            with requests.get(url, stream=True, timeout=120) as reponse:
                reponse.raise_for_status()
                with destination.open("wb") as f:
                    for bloc in reponse.iter_content(chunk_size=8 * 1024 * 1024):
                        f.write(bloc)
            SnowflakeHook(snowflake_conn_id=CONN_ID).run(
                f"PUT file://{destination} @{STAGE} AUTO_COMPRESS=FALSE OVERWRITE=FALSE"
            )
        finally:
            destination.unlink(missing_ok=True)
        return destination.name

    @task
    def copier_dans_la_table(fichier: str) -> None:
        """COPY INTO avec les mêmes options qu'au jour 2 (sans doublon)."""
        SnowflakeHook(snowflake_conn_id=CONN_ID).run(
            f"""
            COPY INTO {TABLE}
              FROM @{STAGE}
              FILES = ('{fichier}')
              FILE_FORMAT = (FORMAT_NAME = {FORMAT_FICHIER})
              MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
              INCLUDE_METADATA = (
                _source_file = METADATA$FILENAME,
                _loaded_at = METADATA$START_SCAN_TIME
              )
              ON_ERROR = ABORT_STATEMENT
            """
        )

    # --- Chargement RAW ---
    fichier = nom_du_fichier()
    url = verifier_disponibilite(fichier)
    nom = telecharger_et_deposer(url)
    copie = copier_dans_la_table(nom)

    controle_raw = check_task("controle_raw_mois_charge", "controles/raw_mois_charge.sql")
    creer_tables = sql_task("creer_tables", "00_tables.sql", split=True)

    with TaskGroup("staging") as staging:
        codes = sql_task("codes_tlc", "staging/codes_tlc.sql", split=True)
        stg_trips = sql_task("stg_yellow_trips", "staging/stg_tlc__yellow_trips.sql")
        stg_zones = sql_task("stg_taxi_zones", "staging/stg_tlc__taxi_zones.sql")
        [codes, stg_trips, stg_zones]

    with TaskGroup("intermediate") as intermediate:
        flagged = sql_task("int_trips_flagged", "intermediate/int_trips__flagged.sql", split=True)
        controle_rejets = check_task("controle_trop_de_rejets", "controles/trop_de_rejets.sql")
        enriched = sql_task("int_trips_enriched", "intermediate/int_trips__enriched.sql", split=True)
        controle_doublons = check_task(
            "controle_trajets_sans_doublon", "controles/trajets_sans_doublon.sql"
        )
        flagged >> controle_rejets >> enriched >> controle_doublons

    with TaskGroup("marts") as marts:
        dims = [
            sql_task("dim_date", "marts/dim_date.sql"),
            sql_task("dim_zone", "marts/dim_zone.sql"),
            sql_task("dim_vendor", "marts/dim_vendor.sql"),
            sql_task("dim_rate_code", "marts/dim_rate_code.sql"),
            sql_task("dim_payment_type", "marts/dim_payment_type.sql"),
        ]
        faits = sql_task("fct_trips", "marts/fct_trips.sql", split=True)
        mart_demand = sql_task("mart_zone_hourly_demand", "marts/mart_zone_hourly_demand.sql")
        mart_revenue = sql_task("mart_daily_revenue", "marts/mart_daily_revenue.sql")
        mart_quality = sql_task("mart_data_quality", "marts/mart_data_quality.sql")

        dims >> faits
        faits >> [mart_demand, mart_revenue]
        # mart_data_quality lit INT_TRIPS__FLAGGED (déjà prêt) ; on le place après les dims
        dims >> mart_quality

    copie >> controle_raw >> creer_tables >> staging >> intermediate >> marts


chargement_yellow_taxi()
