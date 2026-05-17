-- Run this in psql as the postgres superuser:
--   psql -U postgres -f scripts/init_postgres.sql

CREATE USER securevault WITH PASSWORD 'securevault';

CREATE DATABASE securevault_db   OWNER securevault;
CREATE DATABASE securevault_test OWNER securevault;

GRANT ALL PRIVILEGES ON DATABASE securevault_db   TO securevault;
GRANT ALL PRIVILEGES ON DATABASE securevault_test TO securevault;

\echo 'Done. Databases securevault_db and securevault_test created.'