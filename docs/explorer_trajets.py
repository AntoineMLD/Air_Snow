"""Explore le fichier Parquet Yellow Taxi et affiche les infos pour la fiche source.

Usage :
    uv run python docs/explorer_trajets.py
    uv run python docs/explorer_trajets.py yellow_tripdata_2025-01.parquet
"""

from pathlib import Path
import sys

import duckdb


def taille_lisible(chemin: Path) -> str:
    """Retourne la taille du fichier en Mo."""
    mo = chemin.stat().st_size / (1024 * 1024)
    return f"{mo:.0f} Mo"


def explorer(chemin_fichier: Path) -> None:
    """Affiche volume, colonnes, codes et anomalies du fichier Parquet."""
    if not chemin_fichier.exists():
        print(f"Fichier introuvable : {chemin_fichier}")
        sys.exit(1)

    fichier = str(chemin_fichier)
    con = duckdb.connect()

    print("=== IDENTITÉ / VOLUME ===")
    print(f"Fichier : {chemin_fichier.name}")
    print(f"Taille  : {taille_lisible(chemin_fichier)}")
    print(con.sql(f"SELECT COUNT(*) AS lignes FROM '{fichier}'"))
    print(con.sql(f"SELECT COUNT(*) AS colonnes FROM (DESCRIBE SELECT * FROM '{fichier}')"))

    print("\n=== COLONNES (nom + type) ===")
    print(con.sql(f"DESCRIBE SELECT * FROM '{fichier}'"))

    print("\n=== EXEMPLE (1 ligne) ===")
    print(con.sql(f"SELECT * FROM '{fichier}' LIMIT 1"))

    print("\n=== CODES OBSERVÉS ===")
    for colonne in ("VendorID", "RatecodeID", "payment_type", "store_and_fwd_flag"):
        print(f"\n-- {colonne} --")
        print(
            con.sql(
                f"""
                SELECT {colonne} AS valeur, COUNT(*) AS nb
                FROM '{fichier}'
                GROUP BY 1
                ORDER BY 1
                """
            )
        )

    print("\n=== CE QUI SURPREND ===")
    print(
        con.sql(
            f"""
            SELECT
                MIN(tpep_pickup_datetime) AS min_pickup,
                MAX(tpep_pickup_datetime) AS max_pickup,
                COUNT(*) FILTER (WHERE fare_amount < 0) AS fare_negatifs,
                COUNT(*) FILTER (WHERE trip_distance < 0) AS distance_negatives,
                COUNT(*) FILTER (WHERE passenger_count IS NULL) AS passenger_null,
                COUNT(*) FILTER (WHERE RatecodeID IS NULL) AS ratecode_null,
                COUNT(*) FILTER (WHERE payment_type = 0) AS payment_type_0
            FROM '{fichier}'
            """
        )
    )


if __name__ == "__main__":
    # Par défaut : le fichier janvier à la racine du projet
    chemin = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("yellow_tripdata_2025-01.parquet")
    explorer(chemin)
