"""Teste la connexion Snowflake avec l'utilisateur de service (jour 1).

Prérequis :
  - paire de clés dans ~/.ssh/snowflake/
  - utilisateur AIRFLOW_SVC créé avec la clé publique
  - variable d'environnement SNOWFLAKE_ACCOUNT (ex. AGXRVXZ-TI22230)

Usage :
    export SNOWFLAKE_ACCOUNT='AGXRVXZ-TI22230'
    uv run python snowflake/test_connexion.py

Résultat attendu :
    ('AIRFLOW_SVC', 'TRANSFORMER', 'NYC_TAXI_WH')
"""

import os
import sys

import snowflake.connector
from cryptography.hazmat.primitives import serialization


def charger_cle_privee(chemin: str):
    """Charge la clé privée PEM utilisée pour s'authentifier."""
    with open(os.path.expanduser(chemin), "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def tester_connexion() -> None:
    """Se connecte et affiche user / rôle / warehouse actifs."""
    account = os.environ.get("SNOWFLAKE_ACCOUNT")
    if not account:
        print(
            "Missing SNOWFLAKE_ACCOUNT.\n"
            "Example:\n"
            "  export SNOWFLAKE_ACCOUNT='ORGANISATION-COMPTE'\n"
            "  uv run python snowflake/test_connexion.py"
        )
        sys.exit(1)

    private_key = charger_cle_privee("~/.ssh/snowflake/rsa_key.p8")

    conn = snowflake.connector.connect(
        account=account,
        user="AIRFLOW_SVC",
        private_key=private_key,
        role="TRANSFORMER",
        warehouse="NYC_TAXI_WH",
    )
    try:
        row = conn.cursor().execute(
            "SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE()"
        ).fetchone()
        print(row)
    finally:
        conn.close()


if __name__ == "__main__":
    tester_connexion()
