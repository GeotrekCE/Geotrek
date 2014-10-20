-------------------------------------------------------------------------------
-- Schema utilities
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION create_schema_if_not_exist(schemaname varchar) RETURNS void AS $$
BEGIN
    -- We can't use IF NOT EXISTS until PostgreSQL 9.3.
    BEGIN
        EXECUTE 'CREATE SCHEMA '|| quote_ident(schemaname) ||';';
    EXCEPTION
      WHEN OTHERS THEN
        RAISE NOTICE 'Schema exists.';
    END;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION set_schema(tablename varchar, schemaname varchar) RETURNS void AS $$
BEGIN
    -- If schema is already set, an error is raised.
    BEGIN
        EXECUTE 'ALTER TABLE '|| quote_ident(tablename) ||' SET SCHEMA '|| quote_ident(schemaname) ||';';
    EXCEPTION
      WHEN OTHERS THEN
        RAISE NOTICE 'Table already in schema.';
    END;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION set_schema_ft(functionname varchar, schemaname varchar) RETURNS void AS $$
BEGIN
    -- If destination exists, delete!
    EXECUTE 'DROP FUNCTION IF EXISTS ' || schemaname || '.' || functionname || ' CASCADE;';
    -- If schema is already set, an error is raised.
    BEGIN
        EXECUTE 'ALTER FUNCTION '|| functionname ||' SET SCHEMA '|| quote_ident(schemaname) ||';';
    EXCEPTION
      WHEN OTHERS THEN
        RAISE NOTICE 'Function already in schema.';
    END;
END;
$$ LANGUAGE plpgsql;


-------------------------------------------------------------------------------
-- Date trigger functions
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION ft_date_insert() RETURNS trigger AS $$
BEGIN
    NEW.date_insert := statement_timestamp() AT TIME ZONE 'UTC';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION ft_date_update() RETURNS trigger AS $$
BEGIN
    NEW.date_update := statement_timestamp() AT TIME ZONE 'UTC';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

