# Contrôle qualité — janvier 2025

Comparaison entre `MART_DATA_QUALITY` et un comptage manuel
(mêmes règles que `int_trips__flagged.sql` : **une seule raison par trajet**, la première).

## Résultat

| Statut | MART_DATA_QUALITY | Comptage manuel | Écart |
|---|---:|---:|---|
| valid | 3 251 337 | 3 251 337 | 0 |
| amount_non_positive | 130 112 | 130 112 | 0 |
| distance_out_of_range | 90 327 | 90 327 | 0 |
| duration_non_positive | 2 051 | 2 051 | 0 |
| duration_too_long | 1 377 | 1 377 | 0 |
| pickup_outside_file_month | 22 | 22 | 0 |
| **Total** | **3 475 226** | **3 475 226** | **0** |

## Pourquoi un comptage « naïf » diverge

Si on compte chaque anomalie **indépendamment** (un trajet peut être dans plusieurs cases) :

| Anomalie (filtre seul) | Nb |
|---|---:|
| amount_non_positive | 144 998 |
| distance_out_of_range | 91 055 |
| duration_non_positive | 2 051 |
| duration_too_long | 1 377 |
| pickup_outside_file_month | 22 |

Exemple : ~145k montants anormaux en naïf vs 130k dans le mart, parce que certains de ces trajets ont déjà été classés avant (durée / distance) dans le `CASE`.

## Requêtes utilisées

```sql
-- Mart
SELECT status, nb_rows, pct_of_file
FROM NYC_TAXI.MARTS.MART_DATA_QUALITY
WHERE source_file_month = '2025-01-01'
ORDER BY nb_rows DESC;

-- Manuel (même ordre de règles)
WITH s AS (
  SELECT * FROM NYC_TAXI.STAGING.STG_TLC__YELLOW_TRIPS
  WHERE source_file_month = '2025-01-01'
),
flagged AS (
  SELECT
    CASE
      WHEN pickup_at IS NULL OR dropoff_at IS NULL THEN 'timestamp_null'
      WHEN dropoff_at <= pickup_at THEN 'duration_non_positive'
      WHEN DATEDIFF('second', pickup_at, dropoff_at) > 180 * 60 THEN 'duration_too_long'
      WHEN DATE_TRUNC('month', pickup_at) <> source_file_month THEN 'pickup_outside_file_month'
      WHEN trip_distance_miles <= 0 OR trip_distance_miles > 100 THEN 'distance_out_of_range'
      WHEN fare_amount < 0 OR total_amount <= 0 THEN 'amount_non_positive'
      WHEN pickup_zone_key IS NULL OR dropoff_zone_key IS NULL THEN 'zone_null'
      ELSE 'valid'
    END AS status
  FROM s
)
SELECT status, COUNT(*) AS nb
FROM flagged
GROUP BY 1
ORDER BY nb DESC;
```
