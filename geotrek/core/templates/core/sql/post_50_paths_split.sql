CREATE FUNCTION {{ schema_geotrek }}.paths_snap_extremities() RETURNS trigger SECURITY DEFINER AS $$
DECLARE
    linestart geometry;
    lineend geometry;
    other geometry;
    closest geometry;
    result geometry;
    newline geometry[];
    d float8;

    DISTANCE float8;
BEGIN
    DISTANCE := {{ PATH_SNAPPING_DISTANCE }};

    linestart := ST_StartPoint(NEW.geom);
    lineend := ST_EndPoint(NEW.geom);

    closest := NULL;
    SELECT ST_ClosestPoint(geom, linestart), geom INTO closest, other
      FROM core_path
      WHERE geom && ST_Buffer(NEW.geom, DISTANCE * 2)
        AND id != NEW.id
        AND ST_Distance(geom, linestart) < DISTANCE
      ORDER BY ST_Distance(geom, linestart)
      LIMIT 1;

    IF closest IS NULL THEN
        result := linestart;
    ELSE
        result := closest;
        d := DISTANCE;
        FOR i IN 1..ST_NPoints(other) LOOP
            IF ST_Distance(closest, ST_PointN(other, i)) < DISTANCE AND ST_Distance(closest, ST_PointN(other, i)) < d THEN
                d := ST_Distance(closest, ST_PointN(other, i));
                result := ST_PointN(other, i);
            END IF;
        END LOOP;
        IF NOT ST_Equals(linestart, result) THEN
            -- RAISE NOTICE 'Snapped start % to %, from %', ST_AsText(linestart), ST_AsText(result), ST_AsText(other);
        END IF;
    END IF;
    newline := array_append(newline, result);

    FOR i IN 2..ST_NPoints(NEW.geom)-1 LOOP
        newline := array_append(newline, ST_PointN(NEW.geom, i));
    END LOOP;

    closest := NULL;
    SELECT ST_ClosestPoint(geom, lineend), geom INTO closest, other

      FROM core_path
      WHERE geom && ST_Buffer(NEW.geom, DISTANCE * 2)
        AND id != NEW.id
        AND ST_Distance(geom, lineend) < DISTANCE
      ORDER BY ST_Distance(geom, lineend)
      LIMIT 1;
    IF closest IS NULL THEN
        result := lineend;
    ELSE
        result := closest;
        d := DISTANCE;
        FOR i IN 1..ST_NPoints(other) LOOP
            IF ST_Distance(closest, ST_PointN(other, i)) < DISTANCE AND ST_Distance(closest, ST_PointN(other, i)) < d THEN
                d := ST_Distance(closest, ST_PointN(other, i));
                result := ST_PointN(other, i);
            END IF;
        END LOOP;
        IF NOT ST_Equals(lineend, result) THEN
            -- RAISE NOTICE 'Snapped end % to %, from %', ST_AsText(lineend), ST_AsText(result), ST_AsText(other);
        END IF;
    END IF;
    newline := array_append(newline, result);

    -- RAISE NOTICE 'New geom %', ST_AsText(ST_MakeLine(newline));
    NEW.geom := ST_MakeLine(newline);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER core_path_00_snap_geom_iu_tgr
BEFORE INSERT OR UPDATE OF geom ON core_path
FOR EACH ROW EXECUTE PROCEDURE paths_snap_extremities();


-------------------------------------------------------------------------------
-- Split paths when crossing each other
-------------------------------------------------------------------------------

CREATE FUNCTION {{ schema_geotrek }}.paths_topology_intersect_split() RETURNS trigger SECURITY DEFINER AS $$
DECLARE
    path record;
    tid_clone integer;
    t_count integer;
    element RECORD;
    num_order integer;
    existing_et integer[];
    t_geom geometry;

    fraction float8;
    a float8;
    b float8;
    segment geometry;
    newgeom geometry;

    intersections_on_new float8[];
    intersections_on_current float8[];
BEGIN

    -- Copy original geometry
    newgeom := NEW.geom;
    intersections_on_new := ARRAY[0::float];

    -- Iterate paths intersecting, excluding those touching only by extremities
    FOR path IN SELECT *
                   FROM core_path t
                   WHERE id != NEW.id
                         AND draft = FALSE
                         AND NEW.draft = FALSE
                         AND ST_DWithin(t.geom, NEW.geom, 0)
                         AND GeometryType(ST_Intersection(geom, NEW.geom)) NOT IN ('LINESTRING', 'MULTILINESTRING')
    LOOP

        -- RAISE NOTICE '%-% (%) intersects %-% (%) : %', NEW.id, NEW.name, ST_AsText(NEW.geom), path.id, path.name, ST_AsText(path.geom), ST_AsText(ST_Intersection(path.geom, NEW.geom));

        -- Locate intersecting point(s) on NEW, for later use
        FOR fraction IN SELECT ST_LineLocatePoint(NEW.geom,
                                                  (ST_Dump(ST_Intersection(path.geom, NEW.geom))).geom)
                        WHERE NOT ST_Equals(ST_StartPoint(NEW.geom), ST_StartPoint(path.geom))
                          AND NOT ST_Equals(ST_StartPoint(NEW.geom), ST_EndPoint(path.geom))
                          AND NOT ST_Equals(ST_EndPoint(NEW.geom), ST_StartPoint(path.geom))
                          AND NOT ST_Equals(ST_EndPoint(NEW.geom), ST_EndPoint(path.geom))
        LOOP
            intersections_on_new := array_append(intersections_on_new, fraction);
        END LOOP;
        intersections_on_new := array_append(intersections_on_new, 1::float);

        -- Sort intersection points and remove duplicates (0 and 1 can appear twice)
        SELECT array_agg(sub.fraction) INTO intersections_on_new
            FROM (SELECT DISTINCT unnest(intersections_on_new) AS fraction ORDER BY fraction) AS sub;

        -- Locate intersecting point(s) on current path (array of  : {0, 0.32, 0.89, 1})
        intersections_on_current := ARRAY[0::float];

        IF ST_DWithin(ST_StartPoint(NEW.geom), path.geom, 0)
        THEN
            intersections_on_current := array_append(intersections_on_current,
                                                 ST_LineLocatePoint(path.geom,
                                                                      ST_ClosestPoint(path.geom, ST_StartPoint(NEW.geom))));
        END IF;

        IF ST_DWithin(ST_EndPoint(NEW.geom), path.geom, 0)
        THEN
            intersections_on_current := array_append(intersections_on_current,
                                                 ST_LineLocatePoint(path.geom,
                                                                      ST_ClosestPoint(path.geom, ST_EndPoint(NEW.geom))));

        END IF;
        -- RAISE NOTICE 'EEE : %', array_to_string(intersections_on_current, ', ');
        FOR fraction IN SELECT ST_LineLocatePoint(path.geom, (ST_Dump(ST_Intersection(path.geom, NEW.geom))).geom)
        LOOP
            intersections_on_current := array_append(intersections_on_current, fraction);
        END LOOP;
        intersections_on_current := array_append(intersections_on_current, 1::float);

        -- Sort intersection points and remove duplicates (0 and 1 can appear twice)
        SELECT array_agg(sub.fraction) INTO intersections_on_current
            FROM (SELECT DISTINCT unnest(intersections_on_current) AS fraction ORDER BY fraction) AS sub;



        IF array_length(intersections_on_new, 1) > 2 AND array_length(intersections_on_current, 1) > 2 THEN
            -- If both intersects, one is enough, since split trigger will be applied recursively.
            intersections_on_new := ARRAY[]::float[];
        END IF;

    --------------------------------------------------------------------
    -- 1. Handle NEW intersecting with existing paths
    --------------------------------------------------------------------

        -- Skip if intersections are 0,1 (means not crossing)
        IF array_length(intersections_on_new, 1) > 2 THEN
            -- RAISE NOTICE 'New: % % intersecting on NEW % % : %', NEW.id, NEW.name, path.id, path.name, intersections_on_new;

            FOR i IN 1..(array_length(intersections_on_new, 1) - 1)
            LOOP
                a := intersections_on_new[i];
                b := intersections_on_new[i+1];

                segment := ST_LineSubstring(newgeom, a, b);

                IF coalesce(ST_Length(segment), 0) < 1 THEN
                     intersections_on_new[i+1] := a;
                     CONTINUE;
                END IF;

                IF i = 1 THEN
                    -- First segment : shrink it !
                    SELECT COUNT(*) INTO t_count FROM core_path WHERE ST_Contains(ST_Buffer(segment,0.0001),geom);
                    IF t_count = 0 THEN
                        -- RAISE NOTICE 'New: Skrink %-% (%) to %', NEW.id, NEW.name, ST_AsText(NEW.geom), ST_AsText(segment);
                        UPDATE core_path SET geom = segment WHERE id = NEW.id;
                    END IF;
                ELSE
                    -- Next ones : create clones !
                    SELECT COUNT(*) INTO t_count FROM core_path WHERE ST_Contains(ST_Buffer(segment,0.0001),geom);
                    IF t_count = 0 THEN
                        -- RAISE NOTICE 'New: Create clone of %-% with geom %', NEW.id, NEW.name, ST_AsText(segment);
                        INSERT INTO core_path (structure_id,
                                                 visible,
                                                 valid,
                                                 name,
                                                 comments,
                                                 source_id,
                                                 stake_id,
                                                 geom_cadastre,
                                                 departure,
                                                 arrival,
                                                 comfort_id,
                                                 eid,
                                                 geom,
                                                 draft)
                            VALUES (NEW.structure_id,
                                    NEW.visible,
                                    NEW.valid,
                                    NEW.name,
                                    NEW.comments,
                                    NEW.source_id,
                                    NEW.stake_id,
                                    NEW.geom_cadastre,
                                    NEW.departure,
                                    NEW.arrival,
                                    NEW.comfort_id,
                                    NEW.eid,
                                    segment,
                                    NEW.draft)
                            RETURNING id INTO tid_clone;
                    END IF;
                END IF;
            END LOOP;

            -- Recursive triggers did all the work. Stop here.
            RETURN NULL;
        END IF;


    --------------------------------------------------------------------
    -- 2. Handle paths intersecting with NEW
    --------------------------------------------------------------------

        -- Skip if intersections are 0,1 (means not crossing)
        IF array_length(intersections_on_current, 1) > 2 THEN
            -- RAISE NOTICE 'Current: % % intersecting on current % % : %', NEW.id, NEW.name, path.id, path.name, intersections_on_current;

            SELECT array_agg(id) INTO existing_et FROM core_pathaggregation et WHERE et.path_id = path.id;
             IF existing_et IS NOT NULL THEN
                 -- RAISE NOTICE 'Existing topologies id for %-% (%): %', path.id, path.name, ST_AsText(path.geom), existing_et;
             END IF;

            FOR i IN 1..(array_length(intersections_on_current, 1) - 1)
            LOOP
                a := intersections_on_current[i];
                b := intersections_on_current[i+1];

                segment := ST_LineSubstring(path.geom, a, b);

                IF coalesce(ST_Length(segment), 0) < 1 THEN
                     intersections_on_new[i+1] := a;
                     CONTINUE;
                END IF;

                IF i = 1 THEN
                    -- First segment : shrink it !
                    SELECT geom INTO t_geom FROM core_path WHERE id = path.id;
                    IF NOT ST_Equals(t_geom, segment) THEN
                        -- RAISE NOTICE 'Current: Skrink %-% (%) to %', path.id, path.name, ST_AsText(path.geom), ST_AsText(segment);
                        UPDATE core_path SET geom = segment WHERE id = path.id;
                    END IF;
                ELSE
                    -- Next ones : create clones !
                    SELECT COUNT(*) INTO t_count FROM core_path WHERE ST_Contains(ST_Buffer(geom,0.0001),segment);
                    IF t_count = 0 THEN
                        -- RAISE NOTICE 'Current: Create clone of %-% (%) with geom %', path.id, path.name, ST_AsText(path.geom), ST_AsText(segment);
                        INSERT INTO core_path (structure_id,
                                                 visible,
                                                 valid,
                                                 name,
                                                 comments,
                                                 source_id,
                                                 stake_id,
                                                 geom_cadastre,
                                                 departure,
                                                 arrival,
                                                 comfort_id,
                                                 eid,
                                                 geom,
                                                 draft)
                            VALUES (path.structure_id,
                                    path.visible,
                                    path.valid,
                                    path.name,
                                    path.comments,
                                    path.source_id,
                                    path.stake_id,
                                    path.geom_cadastre,
                                    path.departure,
                                    path.arrival,
                                    path.comfort_id,
                                    path.eid,
                                    segment,
                                    path.draft)
                            RETURNING id INTO tid_clone;

                        -- Copy N-N relations
                        INSERT INTO core_path_networks (path_id, network_id)
                            SELECT tid_clone, tr.network_id
                            FROM core_path_networks tr
                            WHERE tr.path_id = path.id;
                        INSERT INTO core_path_usages (path_id, usage_id)
                            SELECT tid_clone, tr.usage_id
                            FROM core_path_usages tr
                            WHERE tr.path_id = path.id;

                        -- Copy topologies overlapping start/end
                        FOR element IN SELECT
                                tid_clone,
                                et.topo_object_id,
                                CASE WHEN start_position <= end_position THEN
                                    (greatest(a, start_position) - a) / (b - a)
                                ELSE
                                    (least(b, start_position) - a) / (b - a)
                                END AS start_position,
                                CASE WHEN start_position <= end_position THEN
                                    (least(b, end_position) - a) / (b - a)
                                ELSE
                                    (greatest(a, end_position) - a) / (b - a)
                                END AS end_position,
                                et."order"
                            FROM core_pathaggregation et,
                                 core_topology e
                            WHERE et.topo_object_id = e.id
                                  AND et.path_id = path.id
                                  AND ((least(start_position, end_position) < b AND greatest(start_position, end_position) > a) OR       -- Overlapping
                                       (start_position = end_position AND start_position = a AND "offset" = 0)) -- Point
                        LOOP
                            SELECT count(*) INTO num_order FROM core_pathaggregation et WHERE et.topo_object_id = element.topo_object_id AND et."order" = element."order";
                            IF num_order = 1
                            THEN
                                 UPDATE core_pathaggregation SET "order" = "order" + 1 WHERE topo_object_id = element.topo_object_id AND "order" > element."order";
                                 INSERT INTO core_pathaggregation (path_id, topo_object_id, start_position, end_position, "order")
                                 VALUES (tid_clone, element.topo_object_id, element.start_position, element.end_position, element."order" + 1);
                            ELSE
                                INSERT INTO core_pathaggregation (path_id, topo_object_id, start_position, end_position, "order")
                                VALUES (tid_clone, element.topo_object_id, element.start_position, element.end_position, element."order");
                            END IF;
                        END LOOP;
                        GET DIAGNOSTICS t_count = ROW_COUNT;
                        IF t_count > 0 THEN
                            -- RAISE NOTICE 'Duplicated % topologies of %-% (%) on [% ; %] for %-% (%)', t_count, path.id, path.name, ST_AsText(path.geom), a, b, tid_clone, path.name, ST_AsText(segment);
                        END IF;
                        -- Special case : point topology at the end of path
                        IF b = 1 THEN
                            SELECT geom INTO t_geom FROM core_path WHERE id = path.id;
                            fraction := ST_LineLocatePoint(segment, ST_EndPoint(path.geom));
                            INSERT INTO core_pathaggregation (path_id, topo_object_id, start_position, end_position)
                                SELECT tid_clone, topo_object_id, start_position, end_position
                                FROM core_pathaggregation et,
                                     core_topology e
                                WHERE et.topo_object_id = e.id AND
                                      et.path_id = path.id AND
                                      start_position = end_position AND
                                      start_position = 1 AND
                                      "offset" = 0;
                            GET DIAGNOSTICS t_count = ROW_COUNT;
                            IF t_count > 0 THEN
                                -- RAISE NOTICE 'Duplicated % point topologies of %-% (%) on intersection at the end of %-% (%) at [%]', t_count, path.id, path.name, ST_AsText(t_geom), tid_clone, path.name, ST_AsText(segment), fraction;
                            END IF;
                        END IF;
                        -- Special case : point topology exactly where NEW path intersects
                        IF a > 0 THEN
                            fraction := ST_LineLocatePoint(NEW.geom, ST_LineInterpolatePoint(path.geom, a));
                            INSERT INTO core_pathaggregation (path_id, topo_object_id, start_position, end_position, "order")
                                SELECT NEW.id, et.topo_object_id, fraction, fraction, "order"
                                FROM core_pathaggregation et,
                                     core_topology e
                                WHERE et.topo_object_id = e.id
                                  AND et.path_id = path.id
                                  AND start_position = end_position AND start_position = a
                                  AND "offset" = 0;
                            GET DIAGNOSTICS t_count = ROW_COUNT;
                            IF t_count > 0 THEN
                                -- RAISE NOTICE 'Duplicated % point topologies of %-% (%) on intersection by %-% (%) at [%]', t_count, path.id, path.name, ST_AsText(path.geom), NEW.id, NEW.name, ST_AsText(NEW.geom), a;
                            END IF;
                        END IF;

                    END IF;
                END IF;
            END LOOP;


            -- For each existing point topology with offset, re-attach it
            -- to the closest path, among those splitted.
            WITH existing_rec AS (SELECT MAX(et.id) AS id, e."offset", e.geom
                                    FROM core_pathaggregation et,
                                         core_topology e
                                   WHERE et.topo_object_id = e.id
                                     AND e."offset" > 0
                                     AND et.path_id = path.id
                                     AND et.id = ANY(existing_et)
                                     GROUP BY e.id, e."offset", e.geom
                                     HAVING COUNT(et.id) = 1 AND BOOL_OR(et.start_position = et.end_position)),
                 closest_path AS (SELECT er.id AS et_id, t.id AS closest_id
                                    FROM core_path t, existing_rec er
                                   WHERE t.id != path.id
                                     AND ST_Distance(er.geom, t.geom) < er."offset"
                                ORDER BY ST_Distance(er.geom, t.geom)
                                   LIMIT 1)
                UPDATE core_pathaggregation SET path_id = closest_id
                  FROM closest_path
                 WHERE id = et_id;
            GET DIAGNOSTICS t_count = ROW_COUNT;
            IF t_count > 0 THEN
                -- Update geom of affected paths to trigger update_topology_geom_when_path_changes()
                UPDATE core_path t SET geom = geom
                  FROM core_pathaggregation et
                 WHERE t.id = et.path_id
                   AND et.start_position = et.end_position
                   AND et.id = ANY(existing_et);
            END IF;

            -- Update point topologies at intersection
            -- Trigger core_pathaggregation_junction_point_iu_tgr
            UPDATE core_pathaggregation et SET start_position = start_position
             WHERE et.path_id = NEW.id
               AND start_position = end_position;

            -- Now handle first path topologies
            a := intersections_on_current[1];
            b := intersections_on_current[2];
            DELETE FROM core_pathaggregation et WHERE et.path_id = path.id
                                                 AND id = ANY(existing_et)
                                                 AND (least(start_position, end_position) > b OR greatest(start_position, end_position) < a);
            GET DIAGNOSTICS t_count = ROW_COUNT;
            IF t_count > 0 THEN
                -- RAISE NOTICE 'Removed % topologies of %-% on [% ; %]', t_count, path.id,  path.name, a, b;
            END IF;

            -- Update topologies overlapping
            UPDATE core_pathaggregation et SET
                start_position = CASE WHEN start_position / (b - a) > 1 THEN 1 ELSE start_position / (b - a) END,
                end_position = CASE WHEN end_position / (b - a) > 1 THEN 1 ELSE end_position / (b - a) END
                WHERE et.path_id = path.id
                AND least(start_position, end_position) <= b AND greatest(start_position, end_position) >= a;
            GET DIAGNOSTICS t_count = ROW_COUNT;
            IF t_count > 0 THEN
                -- RAISE NOTICE 'Updated % topologies of %-% on [% ; %]', t_count, path.id,  path.name, a, b;
            END IF;
        END IF;


    END LOOP;

    IF array_length(intersections_on_new, 1) > 0 OR array_length(intersections_on_current, 1) > 0 THEN
        -- RAISE NOTICE 'Done %-% (%).', NEW.id, NEW.name, ST_AsText(NEW.geom);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER core_path_10_split_geom_iu_tgr
AFTER INSERT OR UPDATE OF geom, draft ON core_path
FOR EACH ROW EXECUTE PROCEDURE paths_topology_intersect_split();
