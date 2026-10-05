# Réponse à la direction d'Hudson Cab Partners

## La question

Où et quand la demande de taxis jaunes est-elle la plus forte à New York, et combien rapporte un trajet selon la zone, l'heure et le mode de paiement ?

## La requête

```sql
-- Demande moyenne par jour : zone × heure × type de jour
-- Table mart construite pour cette question métier.
SELECT
    pickup_zone_name AS zone,
    pickup_borough AS borough,
    pickup_hour AS heure,
    IFF(is_weekend, 'weekend', 'semaine') AS type_jour,
    nb_trips,
    avg_trips_per_day,
    avg_revenue_per_trip,
    avg_fare,
    avg_distance_miles,
    avg_tip_rate_pct_card
FROM NYC_TAXI.MARTS.MART_ZONE_HOURLY_DEMAND
ORDER BY avg_trips_per_day DESC, nb_trips DESC
LIMIT 10;
```

Complément paiement (sur tous les trajets valides) :

```sql
SELECT
    p.payment_type_label,
    COUNT(*) AS nb_trips,
    ROUND(AVG(f.total_amount), 2) AS avg_revenue_per_trip
FROM NYC_TAXI.MARTS.FCT_TRIPS f
JOIN NYC_TAXI.MARTS.DIM_PAYMENT_TYPE p
  ON p.payment_type_key = f.payment_type_key
GROUP BY 1
ORDER BY nb_trips DESC;
```

## Le résultat : les 10 premières lignes

| Zone | Borough | Heure | Type jour | Trajets/jour (moy.) | Recette moy./trajet | Distance moy. (mi) |
|---|---|---|---|---|---|---|
| East Village | Manhattan | 0 | weekend | 738,0 | 22,84 $ | 2,34 |
| East Village | Manhattan | 1 | weekend | 725,7 | 22,11 $ | 2,37 |
| Midtown Center | Manhattan | 18 | semaine | 596,4 | 24,98 $ | 1,93 |
| Midtown Center | Manhattan | 17 | semaine | 571,9 | 30,06 $ | 2,01 |
| West Village | Manhattan | 0 | weekend | 559,1 | 23,14 $ | 2,27 |
| Midtown Center | Manhattan | 20 | semaine | 534,5 | 22,81 $ | 2,24 |
| West Village | Manhattan | 1 | weekend | 519,4 | 22,57 $ | 2,36 |
| East Village | Manhattan | 2 | weekend | 519,0 | 22,00 $ | 2,46 |
| Midtown Center | Manhattan | 19 | semaine | 512,1 | 24,14 $ | 2,00 |
| Midtown Center | Manhattan | 21 | semaine | 494,3 | 23,01 $ | 2,34 |

Paiement le plus fréquent : **carte bancaire** (~7,4 M trajets, ~28,3 $ en moyenne), devant Flex Fare et cash.

## Ce qu'il faut en retenir

1. La demande culmine le **week-end en fin de nuit** dans l’**East Village** (et West Village), autour de minuit–1 h.
2. En semaine, le pic est plutôt le **soir à Midtown Center** (17 h–21 h), avec une recette moyenne un peu plus élevée (~25–30 $).
3. La majorité des trajets se paient en **carte**, avec un pourboire moyen autour de 25–28 % quand il est enregistré.

## Les limites

- Période couverte : **janvier–mars 2025** uniquement (Yellow Taxi TLC).
- Environ **7 %** des trajets bruts ont été écartés (durée, distance, montants, zones…) : voir `MART_DATA_QUALITY`.
- Les pourboires **cash** ne sont pas dans les données TLC ; la recette cash est donc sous-estimée.
- Les zones sans correspondance dans le lookup sont exclues côté qualité ; les aéroports n’apparaissent pas dans ce top 10 « trajets/jour ».
