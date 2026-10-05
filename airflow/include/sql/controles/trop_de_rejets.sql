-- Moins de max_pct_rejetes % de trajets écartés sur le mois traité.
SELECT
    COUNT_IF(rejection_reason IS NOT NULL) / NULLIF(COUNT(*), 0) * 100
        < {{ params.max_pct_rejetes }}
FROM NYC_TAXI.INTERMEDIATE.INT_TRIPS__FLAGGED
WHERE source_file_month = '{{ ds }}'::date;
