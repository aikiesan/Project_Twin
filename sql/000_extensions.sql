-- Runs once at first container start.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SCHEMA IF NOT EXISTS engine;    -- our tables
CREATE SCHEMA IF NOT EXISTS pilar2b;   -- restored PILAR-2b dump (read-only use)
-- h3-pg and pgrouting need a custom image; decide via ADR before enabling:
-- CREATE EXTENSION h3; CREATE EXTENSION h3_postgis; CREATE EXTENSION pgrouting;
