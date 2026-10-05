-- Infrastructure NYC Taxi (jour 1)
-- À exécuter dans Snowsight avec Run All.
-- Sur un compte d'essai, ACCOUNTADMIN peut remplacer USERADMIN / SYSADMIN.
--
-- Ordre : rôles → warehouse → base → schémas → droits → utilisateur → GRANT rôle

-- =============================================================================
-- 1. Rôles
-- =============================================================================
USE ROLE USERADMIN;

CREATE ROLE IF NOT EXISTS TRANSFORMER
  COMMENT = 'Rôle des outils : chargement RAW et transformations';

-- SYSADMIN hérite du rôle (bonne pratique)
GRANT ROLE TRANSFORMER TO ROLE SYSADMIN;

-- =============================================================================
-- 2. Warehouse, base, schémas
-- =============================================================================
USE ROLE SYSADMIN;

CREATE WAREHOUSE IF NOT EXISTS NYC_TAXI_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Warehouse du pipeline NYC Yellow Taxi';

CREATE DATABASE IF NOT EXISTS NYC_TAXI
  COMMENT = 'Entrepôt médaillon Yellow Taxi';

CREATE SCHEMA IF NOT EXISTS NYC_TAXI.RAW
  COMMENT = 'Copie fidèle des fichiers sources';

CREATE SCHEMA IF NOT EXISTS NYC_TAXI.STAGING
  COMMENT = 'Vues de renommage et tables de codes';

CREATE SCHEMA IF NOT EXISTS NYC_TAXI.INTERMEDIATE
  COMMENT = 'Trajets étiquetés et enrichis';

CREATE SCHEMA IF NOT EXISTS NYC_TAXI.MARTS
  COMMENT = 'Faits, dimensions et tables d analyse';

-- =============================================================================
-- 3. Droits du rôle outils (TRANSFORMER)
-- =============================================================================
-- Calcul
GRANT USAGE, OPERATE ON WAREHOUSE NYC_TAXI_WH TO ROLE TRANSFORMER;

-- Accès à la base
GRANT USAGE ON DATABASE NYC_TAXI TO ROLE TRANSFORMER;

-- RAW : charger (tables, stage, formats de fichier)
GRANT USAGE, CREATE TABLE, CREATE STAGE, CREATE FILE FORMAT
  ON SCHEMA NYC_TAXI.RAW TO ROLE TRANSFORMER;

-- STAGING / INTERMEDIATE / MARTS : créer tables et vues
GRANT USAGE, CREATE TABLE, CREATE VIEW
  ON SCHEMA NYC_TAXI.STAGING TO ROLE TRANSFORMER;

GRANT USAGE, CREATE TABLE, CREATE VIEW
  ON SCHEMA NYC_TAXI.INTERMEDIATE TO ROLE TRANSFORMER;

GRANT USAGE, CREATE TABLE, CREATE VIEW
  ON SCHEMA NYC_TAXI.MARTS TO ROLE TRANSFORMER;

-- =============================================================================
-- 4. Utilisateur de service (après génération de la clé publique)
-- =============================================================================
-- Remplacer <CLE_PUBLIQUE> par le résultat de :
--   grep -v "BEGIN\|END" ~/.ssh/snowflake/rsa_key.pub | tr -d '\n' ; echo
--
USE ROLE USERADMIN;

CREATE USER IF NOT EXISTS AIRFLOW_SVC
  TYPE = SERVICE
  DEFAULT_ROLE = TRANSFORMER
  DEFAULT_WAREHOUSE = NYC_TAXI_WH
  DEFAULT_NAMESPACE = NYC_TAXI.RAW
  RSA_PUBLIC_KEY = '<CLE_PUBLIQUE>'
  COMMENT = 'Compte de service Airflow / scripts Python';

GRANT ROLE TRANSFORMER TO USER AIRFLOW_SVC;

-- Vérifications utiles après exécution :
-- SHOW GRANTS TO ROLE TRANSFORMER; 
-- SHOW GRANTS TO USER AIRFLOW_SVC;
-- SELECT CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME() AS account_identifier;
-- AGXRVXZ-TI22230