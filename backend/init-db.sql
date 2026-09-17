-- Initialize PostGIS extension
-- This runs automatically in the Docker postgis/postgis image
-- but we ensure it's enabled for any PostgreSQL instance
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
