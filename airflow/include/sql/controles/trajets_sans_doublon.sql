-- Aucun trajet en double après dédoublonnage (clé trip_sk unique sur le mois).
SELECT COUNT(*) = COUNT(DISTINCT trip_sk)
FROM NYC_TAXI.INTERMEDIATE.INT_TRIPS__ENRICHED
WHERE source_file_month = '{{ ds }}'::date;
