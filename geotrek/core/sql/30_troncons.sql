-------------------------------------------------------------------------------
-- Force Path default values
-- Django does not translate model default value to
-- database default column values.
-------------------------------------------------------------------------------

ALTER TABLE l_t_troncon ALTER COLUMN date_insert SET DEFAULT now();
ALTER TABLE l_t_troncon ALTER COLUMN date_update SET DEFAULT now();
ALTER TABLE l_t_troncon ALTER COLUMN depart SET DEFAULT '';
ALTER TABLE l_t_troncon ALTER COLUMN arrivee SET DEFAULT '';
ALTER TABLE l_t_troncon ALTER COLUMN valide SET DEFAULT false;
ALTER TABLE l_t_troncon ALTER COLUMN visible SET DEFAULT true;



-------------------------------------------------------------------------------
-- Add spatial index (will boost spatial filters)
-------------------------------------------------------------------------------

DROP INDEX IF EXISTS troncons_geom_idx;
DROP INDEX IF EXISTS l_t_troncon_geom_idx;
CREATE INDEX l_t_troncon_geom_idx ON l_t_troncon USING gist(geom);

DROP INDEX IF EXISTS troncons_start_point_idx;
DROP INDEX IF EXISTS l_t_troncon_start_point_idx;
CREATE INDEX l_t_troncon_start_point_idx ON l_t_troncon USING gist(ST_StartPoint(geom));

DROP INDEX IF EXISTS troncons_end_point_idx;
DROP INDEX IF EXISTS l_t_troncon_end_point_idx;
CREATE INDEX l_t_troncon_end_point_idx ON l_t_troncon USING gist(ST_EndPoint(geom));

DROP INDEX IF EXISTS troncons_geom_cadastre_idx;
DROP INDEX IF EXISTS l_t_troncon_geom_cadastre_idx;
CREATE INDEX l_t_troncon_geom_cadastre_idx ON l_t_troncon USING gist(geom_cadastre);

DROP INDEX IF EXISTS l_t_troncon_geom_3d_idx;
CREATE INDEX l_t_troncon_geom_3d_idx ON l_t_troncon USING gist(geom_3d);

-------------------------------------------------------------------------------
-- Keep dates up-to-date
-------------------------------------------------------------------------------

DROP TRIGGER IF EXISTS l_t_troncon_date_insert_tgr ON l_t_troncon;
CREATE TRIGGER l_t_troncon_date_insert_tgr
    BEFORE INSERT ON l_t_troncon
    FOR EACH ROW EXECUTE PROCEDURE ft_date_insert();

DROP TRIGGER IF EXISTS l_t_troncon_date_update_tgr ON l_t_troncon;
CREATE TRIGGER l_t_troncon_date_update_tgr
    BEFORE INSERT OR UPDATE ON l_t_troncon
    FOR EACH ROW EXECUTE PROCEDURE ft_date_update();


-------------------------------------------------------------------------------
-- Check overlapping paths
-------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION check_path_not_overlap(pid integer, line geometry) RETURNS BOOL AS $$
DECLARE
    t_count integer;
    tolerance float;
BEGIN
    -- Note: I gave up with the idea of checking almost overlap/touch.

    -- tolerance := 1.0;
    -- Crossing and extremity touching is OK.
    -- Overlapping and --almost overlapping-- is KO.
    SELECT COUNT(*) INTO t_count
    FROM l_t_troncon
    WHERE pid != id
      AND ST_GeometryType(ST_intersection(geom, line)) IN ('ST_LineString', 'ST_MultiLineString');
      -- not extremity touching
      -- AND ST_Touches(geom, line) = false
      -- not crossing
      -- AND ST_GeometryType(ST_intersection(geom, line)) NOT IN ('ST_Point', 'ST_MultiPoint')
      -- overlap is a line
      -- AND ST_GeometryType(ST_intersection(geom, ST_buffer(line, tolerance))) IN ('ST_LineString', 'ST_MultiLineString')
      -- not almost touching, at most twice
      -- AND       ST_Length(ST_intersection(geom, ST_buffer(line, tolerance))) > (4 * tolerance);
    RETURN t_count = 0;
END;
$$ LANGUAGE plpgsql;


-------------------------------------------------------------------------------
-- Update geometry of related topologies
-------------------------------------------------------------------------------

DROP TRIGGER IF EXISTS l_t_troncon_evenements_geom_u_tgr ON l_t_troncon;
DROP TRIGGER IF EXISTS l_t_troncon_90_evenements_geom_u_tgr ON l_t_troncon;

CREATE OR REPLACE FUNCTION update_evenement_geom_when_troncon_changes() RETURNS trigger AS $$
<<fn>>
DECLARE
    eid integer;
    egeom geometry;
    pk_debut float;
    pk_fin float;
    linear_offset float;
    side_offset float;
BEGIN

    -- If currently shrinking path, don't do anything.
    IF NEW.remarques LIKE '%~' THEN
        RETURN NULL;
    END IF;

    -- Point topologies:
    -- Update pk_debut, pk_fin if not at beginning or end of path
    -- Change in ``e_r_evenement_troncon`` will trigger ``update_geometry_of_evenement()``
    FOR eid, egeom IN SELECT e.id, e.geom
               FROM e_r_evenement_troncon et JOIN e_t_evenement e ON (et.evenement = e.id)
               WHERE et.troncon = NEW.id
                 AND et.pk_debut = et.pk_fin
                 AND et.pk_fin > 0.0 AND et.pk_fin < 1.0
                 AND NOT ft_IsEmpty(e.geom)
    LOOP
        SELECT * INTO linear_offset, side_offset
        FROM ST_InterpolateAlong(NEW.geom, egeom) AS (position float, distance float);

        UPDATE e_r_evenement_troncon SET pk_fin = linear_offset, pk_debut = linear_offset
            WHERE evenement = eid AND troncon = NEW.id;
        UPDATE e_t_evenement SET decallage = side_offset WHERE id = eid;
    END LOOP;


    -- Line topologies:

    -- Geometries of linear topologies that cover 100% of path are updated
    FOR eid IN SELECT DISTINCT e.id
               FROM e_r_evenement_troncon et JOIN e_t_evenement e ON (et.evenement = e.id)
               WHERE et.troncon = NEW.id
                 AND (abs(et.pk_fin - et.pk_debut) = 1.0
                      OR ft_IsEmpty(e.geom))
    LOOP
        PERFORM update_geometry_of_evenement(eid);
    END LOOP;

    -- Update pk_debut, pk_fin when aggregations don't cover 100% of path
    -- Change in ``e_r_evenement_troncon`` will trigger ``update_geometry_of_evenement()``
    FOR eid, egeom, pk_debut, pk_fin IN SELECT e.id, e.geom, et.pk_debut, et.pk_fin
               FROM e_r_evenement_troncon et JOIN e_t_evenement e ON (et.evenement = e.id)
               WHERE et.troncon = NEW.id
                 AND et.pk_debut != et.pk_fin
                 AND abs(et.pk_fin - et.pk_debut) < 1.0
                 AND NOT ft_IsEmpty(e.geom)
    LOOP

        -- If the path was reversed, we have to invert related topologies
        IF ST_Equals(OLD.geom, NEW.geom) AND NOT ST_OrderingEquals(OLD.geom, NEW.geom) THEN
            pk_debut := 1 - pk_debut;
            pk_fin := 1 - pk_fin;
        END IF;

        IF pk_debut < pk_fin THEN
            IF pk_debut > 0 THEN
                -- Only if does not start at beginning of path
                SELECT * INTO linear_offset, side_offset
                    FROM ST_InterpolateAlong(NEW.geom, ST_StartPoint(egeom)) AS (position float, distance float);
                UPDATE e_r_evenement_troncon SET pk_debut = linear_offset, pk_fin = fn.pk_fin
                    WHERE evenement = eid AND troncon = NEW.id;
            END IF;

            IF pk_fin < 1.0 THEN
                -- Only if does not end at end of path
                SELECT * INTO linear_offset, side_offset
                    FROM ST_InterpolateAlong(NEW.geom, ST_EndPoint(egeom)) AS (position float, distance float);
                UPDATE e_r_evenement_troncon SET pk_debut = fn.pk_debut, pk_fin = linear_offset
                    WHERE evenement = eid AND troncon = NEW.id;
            END IF;

        ELSE
            IF pk_debut < 1.0 THEN
                -- Only if does not start at end of path
                SELECT * INTO linear_offset, side_offset
                    FROM ST_InterpolateAlong(NEW.geom, ST_EndPoint(egeom)) AS (position float, distance float);
                UPDATE e_r_evenement_troncon SET pk_debut = linear_offset, pk_fin = fn.pk_fin
                    WHERE evenement = eid AND troncon = NEW.id;
            END IF;

            IF pk_fin > 0.0 THEN
                -- Only if does not end at beginning of path
                SELECT * INTO linear_offset, side_offset
                    FROM ST_InterpolateAlong(NEW.geom, ST_StartPoint(egeom)) AS (position float, distance float);
                UPDATE e_r_evenement_troncon SET pk_debut = fn.pk_debut, pk_fin = linear_offset
                    WHERE evenement = eid AND troncon = NEW.id;
            END IF;

        END IF;
    END LOOP;


    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER l_t_troncon_90_evenements_geom_u_tgr
AFTER UPDATE OF geom ON l_t_troncon
FOR EACH ROW EXECUTE PROCEDURE update_evenement_geom_when_troncon_changes();


-------------------------------------------------------------------------------
-- Ensure paths have valid geometries
-------------------------------------------------------------------------------

ALTER TABLE l_t_troncon DROP CONSTRAINT IF EXISTS troncons_geom_issimple;

ALTER TABLE l_t_troncon DROP CONSTRAINT IF EXISTS l_t_troncon_geom_isvalid;
ALTER TABLE l_t_troncon ADD CONSTRAINT l_t_troncon_geom_isvalid CHECK (ST_IsValid(geom));

ALTER TABLE l_t_troncon DROP CONSTRAINT IF EXISTS l_t_troncon_geom_issimple;
ALTER TABLE l_t_troncon ADD CONSTRAINT l_t_troncon_geom_issimple CHECK (ST_IsSimple(geom));


-------------------------------------------------------------------------------
-- Compute elevation and elevation-based indicators
-------------------------------------------------------------------------------

DROP TRIGGER IF EXISTS l_t_troncon_elevation_iu_tgr ON l_t_troncon;
DROP TRIGGER IF EXISTS l_t_troncon_10_elevation_iu_tgr ON l_t_troncon;

CREATE OR REPLACE FUNCTION elevation_troncon_iu() RETURNS trigger AS $$
DECLARE
    elevation elevation_infos;
BEGIN

    SELECT * FROM ft_elevation_infos(NEW.geom) INTO elevation;
    -- Update path geometry
    NEW.geom_3d := elevation.draped;
    NEW.longueur := ST_3DLength(elevation.draped);
    NEW.pente := elevation.slope;
    NEW.altitude_minimum := elevation.min_elevation;
    NEW.altitude_maximum := elevation.max_elevation;
    NEW.denivelee_positive := elevation.positive_gain;
    NEW.denivelee_negative := elevation.negative_gain;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER l_t_troncon_10_elevation_iu_tgr
BEFORE INSERT OR UPDATE OF geom ON l_t_troncon
FOR EACH ROW EXECUTE PROCEDURE elevation_troncon_iu();


-------------------------------------------------------------------------------
-- Change status of related objects when paths are deleted
-------------------------------------------------------------------------------

DROP TRIGGER IF EXISTS l_t_troncon_related_objects_d_tgr ON l_t_troncon;

CREATE OR REPLACE FUNCTION troncons_related_objects_d() RETURNS trigger AS $$
DECLARE
BEGIN
    -- Mark empty topologies as deleted
    UPDATE e_t_evenement e
        SET supprime = TRUE
        FROM e_r_evenement_troncon et
        WHERE et.evenement = e.id AND et.troncon = OLD.id AND NOT EXISTS(
            SELECT * FROM e_r_evenement_troncon
            WHERE evenement = e.id AND troncon != OLD.id
        );

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER l_t_troncon_related_objects_d_tgr
BEFORE DELETE ON l_t_troncon
FOR EACH ROW EXECUTE PROCEDURE troncons_related_objects_d();


---------------------------------------------------------------------
-- Make sure cache key (base on lastest updated) is refresh on DELETE
---------------------------------------------------------------------

DROP TRIGGER IF EXISTS l_t_troncon_latest_updated_d_tgr ON l_t_troncon;

CREATE OR REPLACE FUNCTION troncon_latest_updated_d() RETURNS trigger AS $$
DECLARE
BEGIN
    -- Touch latest path
    UPDATE l_t_troncon SET date_update = NOW()
    WHERE id IN (SELECT id FROM l_t_troncon ORDER BY date_update DESC LIMIT 1);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER l_t_troncon_latest_updated_d_tgr
AFTER DELETE ON l_t_troncon
FOR EACH ROW EXECUTE PROCEDURE troncon_latest_updated_d();
