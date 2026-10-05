"""Charge un mois Yellow Taxi dans NYC_TAXI.RAW.YELLOW_TRIPDATA (jour 2).

Usage :
    export SNOWFLAKE_ACCOUNT='AGXRVXZ-TI22230'
    uv run python ingestion/charger_mois.py 2025-01

Le script :
  1. utilise le Parquet local s'il existe, sinon le télécharge ;
  2. PUT sur le stage ;
  3. COPY INTO la table (rejouable sans doublon).
"""

import os
import sys
from pathlib import Path

import requests
import snowflake.connector
from cryptography.hazmat.primitives import serialization

URL_BASE = "https://d37ci6vzurychx.cloudfront.net/trip-data"
STAGE = "@NYC_TAXI.RAW.NYC_TAXI_STAGE"
TABLE = "NYC_TAXI.RAW.YELLOW_TRIPDATA"
FORMAT_FICHIER = "NYC_TAXI.RAW.PARQUET_FF"


def connecter():
    """Ouvre une connexion Snowflake avec la clé privée du service."""
    account = os.environ.get("SNOWFLAKE_ACCOUNT")
    if not account:
        print("Missing SNOWFLAKE_ACCOUNT (ex. export SNOWFLAKE_ACCOUNT='ORG-COMPTE')")
        sys.exit(1)

    cle = serialization.load_pem_private_key(
        Path("~/.ssh/snowflake/rsa_key.p8").expanduser().read_bytes(),
        password=None,
    )
    return snowflake.connector.connect(
        account=account,
        user="AIRFLOW_SVC",
        private_key=cle,
        role="TRANSFORMER",
        warehouse="NYC_TAXI_WH",
        database="NYC_TAXI",
        schema="RAW",
    )


def chemin_local(mois: str) -> Path:
    """Retourne le chemin du fichier Parquet pour le mois AAAA-MM."""
    return Path(f"yellow_tripdata_{mois}.parquet").resolve()


def telecharger_si_besoin(mois: str) -> Path:
    """Télécharge le fichier TLC s'il n'est pas déjà sur le disque."""
    destination = chemin_local(mois)
    if destination.exists():
        print(f"Fichier local trouvé : {destination.name}")
        return destination

    url = f"{URL_BASE}/yellow_tripdata_{mois}.parquet"
    print(f"Téléchargement de {url} ...")
    with requests.get(url, stream=True, timeout=120) as reponse:
        reponse.raise_for_status()
        with destination.open("wb") as f:
            for morceau in reponse.iter_content(chunk_size=8 * 1024 * 1024):
                f.write(morceau)
    print(f"Téléchargé : {destination.name}")
    return destination


def charger(conn, fichier: Path) -> int:
    """PUT puis COPY INTO. Renvoie le nombre de lignes chargées."""
    with conn.cursor() as cur:
        cur.execute(
            f"PUT file://{fichier} {STAGE} AUTO_COMPRESS=FALSE OVERWRITE=FALSE"
        )
        print("PUT :", cur.fetchone())

        cur.execute(
            f"""
            COPY INTO {TABLE}
              FROM {STAGE}
              FILES = ('{fichier.name}')
              FILE_FORMAT = (FORMAT_NAME = {FORMAT_FICHIER})
              MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
              INCLUDE_METADATA = (
                _source_file = METADATA$FILENAME,
                _loaded_at = METADATA$START_SCAN_TIME
              )
              ON_ERROR = ABORT_STATEMENT
            """
        )
        lignes = cur.fetchall()
        print("COPY INTO :", lignes)

    chargees = 0
    for ligne in lignes:
        # colonnes typiques : file, status, rows_parsed, rows_loaded, ...
        if len(ligne) > 3 and str(ligne[1]) == "LOADED":
            chargees += int(ligne[3])
    return chargees


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage : uv run python ingestion/charger_mois.py AAAA-MM")
        sys.exit(1)

    mois = sys.argv[1]  # ex. 2025-01
    fichier = telecharger_si_besoin(mois)

    with connecter() as conn:
        n = charger(conn, fichier)
        print(f"{n} lignes chargées pour {mois}")

        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT _source_file, COUNT(*), MIN(_loaded_at)
                FROM {TABLE}
                WHERE _source_file = %s
                GROUP BY 1
                """,
                (fichier.name,),
            )
            print("Vérification :", cur.fetchone())


if __name__ == "__main__":
    main()
