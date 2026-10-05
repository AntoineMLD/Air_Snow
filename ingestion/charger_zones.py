"""Charge le lookup des zones TLC dans NYC_TAXI.RAW.TAXI_ZONE_LOOKUP.

Usage :
    export SNOWFLAKE_ACCOUNT='AGXRVXZ-TI22230'
    uv run python ingestion/charger_zones.py
"""

import os
import sys
from pathlib import Path

import requests
import snowflake.connector
from cryptography.hazmat.primitives import serialization

URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
FICHIER = Path("taxi_zone_lookup.csv").resolve()
STAGE = "@NYC_TAXI.RAW.NYC_TAXI_STAGE"
TABLE = "NYC_TAXI.RAW.TAXI_ZONE_LOOKUP"
FORMAT_FICHIER = "NYC_TAXI.RAW.CSV_FF"


def connecter():
    account = os.environ.get("SNOWFLAKE_ACCOUNT")
    if not account:
        print("Missing SNOWFLAKE_ACCOUNT")
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


def telecharger_si_besoin() -> Path:
    if FICHIER.exists():
        print(f"Fichier local trouvé : {FICHIER.name}")
        return FICHIER

    print(f"Téléchargement de {URL} ...")
    reponse = requests.get(URL, timeout=60)
    reponse.raise_for_status()
    FICHIER.write_bytes(reponse.content)
    return FICHIER


def main() -> None:
    fichier = telecharger_si_besoin()

    with connecter() as conn, conn.cursor() as cur:
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
        print("COPY INTO :", cur.fetchall())

        cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
        print("Nombre de zones :", cur.fetchone()[0])


if __name__ == "__main__":
    main()
