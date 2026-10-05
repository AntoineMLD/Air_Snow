-- Couche RAW (jour 2)
-- À exécuter dans Snowsight avec le rôle des OUTILS (pas ACCOUNTADMIN).
-- Run All.

USE ROLE TRANSFORMER;
USE WAREHOUSE NYC_TAXI_WH;
USE DATABASE NYC_TAXI;
USE SCHEMA RAW;

-- =============================================================================
-- 1. Formats de fichier
-- =============================================================================
CREATE OR REPLACE FILE FORMAT PARQUET_FF
  TYPE = PARQUET
  USE_LOGICAL_TYPE = TRUE
  COMMENT = 'Fichiers mensuels Yellow Taxi (logical types pour timestamps)';

CREATE OR REPLACE FILE FORMAT CSV_FF
  TYPE = CSV
  PARSE_HEADER = TRUE
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
  COMMENT = 'Lookup des zones TLC';

-- =============================================================================
-- 2. Stage (dépôt des fichiers avant COPY INTO)
-- =============================================================================
CREATE STAGE IF NOT EXISTS NYC_TAXI_STAGE
  COMMENT = 'Dépôt des fichiers TLC avant chargement RAW';

-- =============================================================================
-- 3. Tables RAW (noms imposés par CONTRAT_RAW.md)
-- FLOAT pour les montants : NUMBER sans décimales arrondirait.
-- =============================================================================
CREATE TABLE IF NOT EXISTS YELLOW_TRIPDATA (
  vendorid                 NUMBER,
  tpep_pickup_datetime     TIMESTAMP_NTZ,
  tpep_dropoff_datetime    TIMESTAMP_NTZ,
  passenger_count          NUMBER,
  trip_distance            FLOAT,
  ratecodeid               NUMBER,
  store_and_fwd_flag       VARCHAR,
  pulocationid             NUMBER,
  dolocationid             NUMBER,
  payment_type             NUMBER,
  fare_amount              FLOAT,
  extra                    FLOAT,
  mta_tax                  FLOAT,
  tip_amount               FLOAT,
  tolls_amount             FLOAT,
  improvement_surcharge    FLOAT,
  total_amount             FLOAT,
  congestion_surcharge     FLOAT,
  airport_fee              FLOAT,
  cbd_congestion_fee       FLOAT,
  _source_file             VARCHAR,
  _loaded_at               TIMESTAMP_NTZ
);

CREATE TABLE IF NOT EXISTS TAXI_ZONE_LOOKUP (
  locationid               NUMBER,
  borough                  VARCHAR,
  zone                     VARCHAR,
  service_zone             VARCHAR,
  _source_file             VARCHAR,
  _loaded_at               TIMESTAMP_NTZ
);

-- Vérifications
SHOW FILE FORMATS IN SCHEMA NYC_TAXI.RAW;
SHOW STAGES IN SCHEMA NYC_TAXI.RAW;
SHOW TABLES IN SCHEMA NYC_TAXI.RAW;
-- Colonne owner : doit être TRANSFORMER
