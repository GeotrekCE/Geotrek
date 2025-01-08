-- Used to ensure extension is enabled even in test database (migrations disabled)
-- Otherwise UUIDs on objects can not be generated on insert (including path splits)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "postgis_raster";
CREATE EXTENSION IF NOT EXISTS "pgrouting" CASCADE;