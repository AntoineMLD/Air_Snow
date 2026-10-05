# Fiche source — Trajets Yellow Taxi (TLC)

Chiffres mesurés avec : `uv run python docs/explorer_trajets.py`

## Identité

| Rubrique | Réponse |
|---|---|
| Nom de la source | Yellow Taxi Trip Records (TLC) |
| Producteur des données | NYC Taxi & Limousine Commission (TLC) |
| Adresse (URL) | https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet |
| Accès (public, authentifié) | public |
| Format du fichier | Parquet |
| Fréquence de publication | mensuelle |
| Délai entre la période couverte et la publication | ~2 mois (annoncé par la TLC) ; ~2,5 mois pour janvier 2025 (fichier modifié le 23/04/2025) |

## Volume mesuré

| Fichier | Taille | Nombre de lignes | Nombre de colonnes | Outil et commande utilisés |
|---|---|---|---|---|
| yellow_tripdata_2025-01.parquet | 56 Mo | 3 475 226 | 20 | `uv run python docs/explorer_trajets.py` |

## Colonnes

Source des significations : `data_dictionary_trip_records_yellow.pdf` (TLC, 18 mars 2025).

| Colonne | Type dans le fichier | Signification | Exemple de valeur |
|---|---|---|---|
| VendorID | INTEGER | Code du fournisseur TPEP qui a fourni l’enregistrement | 1 |
| tpep_pickup_datetime | TIMESTAMP | Date et heure d’engagement du compteur | 2025-01-01 00:18:38 |
| tpep_dropoff_datetime | TIMESTAMP | Date et heure de désengagement du compteur | 2025-01-01 00:26:59 |
| passenger_count | BIGINT | Nombre de passagers dans le véhicule | 1 |
| trip_distance | DOUBLE | Distance du trajet en miles (taximètre) | 1.6 |
| RatecodeID | BIGINT | Code tarifaire final en vigueur à la fin du trajet | 1 |
| store_and_fwd_flag | VARCHAR | Trajet stocké en mémoire véhicule faute de connexion, puis transmis | N |
| PULocationID | INTEGER | Zone TLC où le compteur a été engagé | 229 |
| DOLocationID | INTEGER | Zone TLC où le compteur a été désengagé | 237 |
| payment_type | BIGINT | Code du mode de paiement du passager | 1 |
| fare_amount | DOUBLE | Tarif temps/distance calculé par le compteur | 10.0 |
| extra | DOUBLE | Extras et surcharges diverses | 3.5 |
| mta_tax | DOUBLE | Taxe MTA déclenchée selon le tarif compteur | 0.5 |
| tip_amount | DOUBLE | Pourboire (carte auto-rempli ; cash non inclus) | 3.0 |
| tolls_amount | DOUBLE | Total des péages du trajet | 0.0 |
| improvement_surcharge | DOUBLE | Surcharge d’amélioration (depuis 2015, au flag drop) | 1.0 |
| total_amount | DOUBLE | Montant total facturé (hors pourboires cash) | 18.0 |
| congestion_surcharge | DOUBLE | Surcharge congestion NYS collectée sur le trajet | 2.5 |
| Airport_fee | DOUBLE | Frais aéroport (prise en charge LGA ou JFK uniquement) | 0.0 |
| cbd_congestion_fee | DOUBLE | Frais MTA Congestion Relief Zone (depuis le 5 janv. 2025) | 0.0 |

## Codes

D’après le dictionnaire TLC (18 mars 2025).

| Colonne | Valeur | Signification |
|---|---|---|
| VendorID | 1 | Creative Mobile Technologies, LLC |
| VendorID | 2 | Curb Mobility, LLC |
| VendorID | 6 | Myle Technologies Inc |
| VendorID | 7 | Helix |
| RatecodeID | 1 | Standard rate |
| RatecodeID | 2 | JFK |
| RatecodeID | 3 | Newark |
| RatecodeID | 4 | Nassau or Westchester |
| RatecodeID | 5 | Negotiated fare |
| RatecodeID | 6 | Group ride |
| RatecodeID | 99 | Null/unknown |
| payment_type | 0 | Flex Fare trip |
| payment_type | 1 | Credit card |
| payment_type | 2 | Cash |
| payment_type | 3 | No charge |
| payment_type | 4 | Dispute |
| payment_type | 5 | Unknown |
| payment_type | 6 | Voided trip |
| store_and_fwd_flag | Y | store and forward trip |
| store_and_fwd_flag | N | not a store and forward trip |

## Ce qui a surpris

- ~144 118 trajets avec `fare_amount` négatif.
- ~540 149 trajets avec `passenger_count` NULL (et souvent `payment_type = 0` / `RatecodeID` NULL).
- Des dates hors janvier : pickup dès le 31/12/2024 jusqu’au 01/02/2025 alors que le fichier est étiqueté `2025-01`.
- `cbd_congestion_fee` est une colonne récente (depuis le 5 janvier 2025).
