-- Parcours outdoor

CREATE VIEW {{ schema_geotrek }}.v_outdoor_course_point AS
SELECT a.id,
       b.name AS "Structure",
       c.zoning_city AS "City",
       d.zoning_district AS "District",
       {% for lang in MODELTRANSLATIONS %}
        a.name_{{ lang }} AS "Name {{lang}}",
       {% endfor %}
       g.site AS "Sites",
       i.filieres AS "Sectors",
       h.pratique AS "Practice",
       {% for lang in MODELTRANSLATIONS %}
        a.ratings_description AS "Ratings description",
       {% endfor %}
       e.name AS "Type",
       {% for lang in MODELTRANSLATIONS %}
        a.description_{{ lang }} AS "Description {{ lang }}",
       {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.advice AS "Advice",
        {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.gear_{{ lang }} AS "Gear {{ lang }}",
       {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.equipment_{{ lang }} AS "Equipment {{ lang }}",
       {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.accessibility AS "Accessibility {{ lang }}",
       {% endfor %}
       CASE
           WHEN a.height IS NOT NULL THEN concat(a.height, ' m')
           ELSE NULL
       END AS "Height",
       a.duration AS "Duration",
       a.eid AS "External id",
       {% for lang in MODELTRANSLATIONS %}
           CASE
               WHEN a.published_{{ lang }} IS FALSE THEN 'No'
               WHEN a.published_{{ lang }} IS TRUE THEN 'Yes'
           END AS "Published {{ lang }}",
       {% endfor %}
       concat ('→ ', a.length::numeric(10, 1),' m (↝', st_length(geom_3d)::numeric(10, 1),' m)') AS "Humanize length",
       a.length AS "Length",
       st_length(geom_3d) AS "Length 3d",
       CASE
           WHEN ascent > 0 THEN concat (descent,'m +',ascent,'m (',slope::numeric(10, 1),')')
           WHEN ascent < 0 THEN concat (descent,'m -',ascent,'m (',slope::numeric(10, 1),')')
       END AS "Slope",
       a.min_elevation
       CONCAT (a.min_elevation, 'm') AS "Minimum elevation",
       COCANT (a.max_elevation, 'm') AS "Maximum elevation",
       a.date_insert AS "Insertion date",
       a.date_update AS "Update date",
       ST_CollectionExtract(a.geom, 1) AS geom
FROM outdoor_course a
LEFT JOIN authent_structure b ON a.structure_id = b.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name), ', ', '*') zoning_city,
            a.id
     FROM
         outdoor_course a
     JOIN zoning_city b ON ST_INTERSECTS (st_pointonsurface(a.geom), b.geom)
     GROUP BY a.id) c ON a.id = c.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name), ', ', '*') zoning_district,
            a.id
     FROM
         outdoor_course a
     JOIN zoning_district b ON ST_INTERSECTS (st_pointonsurface(a.geom), b.geom)
     GROUP BY a.id) d ON a.id = d.id 
LEFT JOIN outdoor_coursetype e ON a.type_id = d.id
LEFT JOIN
    (SELECT b.id,
            array_to_string(ARRAY_AGG (c.name), ', ', '*') site
     FROM outdoor_course_parent_sites a
     JOIN outdoor_course b ON a.course_id = b.id
     JOIN outdoor_site c ON a.site_id = c.id
     GROUP BY b.id) g ON a.id = g.id
LEFT JOIN
    (WITH site_pratique AS
         (SELECT b.id,
                 array_to_string(ARRAY_AGG (c.name), ', ', '*') site
          FROM outdoor_course_parent_sites a
          JOIN outdoor_course b ON a.course_id = b.id
          JOIN outdoor_site c ON a.site_id = c.id
          GROUP BY b.id) SELECT a.id,
                                a.site,
                                b.pratique
     FROM site_pratique a
     JOIN
         (WITH pratique AS
              (SELECT c.id,
                      array_to_string(ARRAY_AGG (c.name), ', ', '*') site
               FROM outdoor_course_parent_sites a
               JOIN outdoor_course b ON a.course_id = b.id
               JOIN outdoor_site c ON a.site_id = c.id
               GROUP BY c.id) SELECT a.id,
                                     a.site,
                                     b.pratique
          FROM pratique a
          JOIN
              (SELECT a.id,
                      array_to_string(ARRAY_AGG (b.name), ', ', '*') pratique
               FROM outdoor_site a
               JOIN outdoor_practice b ON a.practice_id = b.id
               GROUP BY a.id) b ON a.id = b.id) b ON a.site= b.site) h ON a.id = h.id
LEFT JOIN
    (WITH site_filieres AS
         (SELECT b.id,
                 array_to_string(ARRAY_AGG (c.name), ', ', '*') site
          FROM outdoor_course_parent_sites a
          JOIN outdoor_course b ON a.course_id = b.id
          JOIN outdoor_site c ON a.site_id = c.id
          GROUP BY b.id) SELECT a.id,
                                a.site,
                                b.filieres
     FROM site_filieres a
     JOIN
         (WITH filieres AS
              (SELECT c.id,
                      array_to_string(ARRAY_AGG (c.name), ', ', '*') site
               FROM outdoor_course_parent_sites a
               JOIN outdoor_course b ON a.course_id = b.id
               JOIN outdoor_site c ON a.site_id = c.id
               GROUP BY c.id) SELECT a.id,
                                     a.site,
                                     b.filieres
          FROM filieres a
          JOIN
              (SELECT a.id,
                      array_to_string(ARRAY_AGG (c.name), ', ', '*') filieres
               FROM outdoor_site a
               JOIN outdoor_practice b ON a.practice_id = b.id
               JOIN outdoor_sector c ON b.sector_id = c.id
               GROUP BY a.id) b ON a.id = b.id) b ON a.site = b.site) i ON a.id = i.id
WHERE ST_GEOMETRYTYPE(ST_CollectionExtract(a.geom, 1)) IN ('ST_MultiPoint',
                                                           'ST_Point')
    AND ST_AsText(ST_CollectionExtract(a.geom, 1)) != 'MULTIPOINT EMPTY';


CREATE VIEW {{ schema_geotrek }}.v_outdoor_course_polygon AS
SELECT a.id,
       b.name AS "Structure",
       c.zoning_city AS "City",
       d.zoning_district AS "District",
       {% for lang in MODELTRANSLATIONS %}
        a.name_{{ lang }} AS "Name {{lang}}",
       {% endfor %}
       g.site AS "Sites",
       i.filieres AS "Sectors",
       h.pratique AS "Practice",
       {% for lang in MODELTRANSLATIONS %}
        a.ratings_description AS "Ratings description",
       {% endfor %}
       e.name AS "Type",
       {% for lang in MODELTRANSLATIONS %}
        a.description_{{ lang }} AS "Description {{ lang }}",
       {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.advice AS "Advice",
        {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.gear_{{ lang }} AS "Gear {{ lang }}",
       {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.equipment_{{ lang }} AS "Equipment {{ lang }}",
       {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.accessibility AS "Accessibility {{ lang }}",
       {% endfor %}
       CASE
           WHEN a.height IS NOT NULL THEN concat(a.height, ' m')
           ELSE NULL
       END AS "Height",
       a.duration AS "Duration",
       a.eid AS "External id",
       {% for lang in MODELTRANSLATIONS %}
           CASE
               WHEN a.published_{{ lang }} IS FALSE THEN 'No'
               WHEN a.published_{{ lang }} IS TRUE THEN 'Yes'
           END AS "Published {{ lang }}",
       {% endfor %}
       concat ('→ ', a.length::numeric(10, 1),' m (↝', st_length(geom_3d)::numeric(10, 1),' m)') AS "Humanize length",
       a.length AS "Length",
       st_length(geom_3d) AS "Length 3d",
       CASE
           WHEN ascent > 0 THEN concat (descent,'m +',ascent,'m (',slope::numeric(10, 1),')')
           WHEN ascent < 0 THEN concat (descent,'m -',ascent,'m (',slope::numeric(10, 1),')')
       END AS "Slope",
       a.min_elevation
       CONCAT (a.min_elevation, 'm') AS "Minimum elevation",
       COCANT (a.max_elevation, 'm') AS "Maximum elevation",
       a.date_insert AS "Insertion date",
       a.date_update AS "Update date",
       ST_CollectionExtract(a.geom, 1) AS geom
FROM outdoor_course a
LEFT JOIN authent_structure b ON a.structure_id = b.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name), ', ', '*') zoning_city,
            a.id
     FROM
         outdoor_course a
     JOIN zoning_city b ON ST_INTERSECTS (st_pointonsurface(a.geom), b.geom)
     GROUP BY a.id) c ON a.id = c.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name), ', ', '*') zoning_district,
            a.id
     FROM
         outdoor_course a
     JOIN zoning_district b ON ST_INTERSECTS (st_pointonsurface(a.geom), b.geom)
     GROUP BY a.id) d ON a.id = d.id 
LEFT JOIN outdoor_coursetype e ON a.type_id = e.id
LEFT JOIN
    (SELECT b.id,
            array_to_string(ARRAY_AGG (c.name), ', ', '*') site
     FROM outdoor_course_parent_sites a
     JOIN outdoor_course b ON a.course_id = b.id
     JOIN outdoor_site c ON a.site_id = c.id
     GROUP BY b.id) g ON a.id = g.id
LEFT JOIN
    (WITH site_pratique AS
         (SELECT b.id,
                 array_to_string(ARRAY_AGG (c.name), ', ', '*') site
          FROM outdoor_course_parent_sites a
          JOIN outdoor_course b ON a.course_id = b.id
          JOIN outdoor_site c ON a.site_id = c.id
          GROUP BY b.id) SELECT a.id,
                                a.site,
                                b.pratique
     FROM site_pratique a
     JOIN
         (WITH pratique AS
              (SELECT c.id,
                      array_to_string(ARRAY_AGG (c.name), ', ', '*') site
               FROM outdoor_course_parent_sites a
               JOIN outdoor_course b ON a.course_id = b.id
               JOIN outdoor_site c ON a.site_id = c.id
               GROUP BY c.id) SELECT a.id,
                                     a.site,
                                     b.pratique
          FROM pratique a
          JOIN
              (SELECT a.id,
                      array_to_string(ARRAY_AGG (b.name), ', ', '*') pratique
               FROM outdoor_site a
               JOIN outdoor_practice b ON a.practice_id = b.id
               GROUP BY a.id) b ON a.id = b.id) b ON a.site= b.site) h ON a.id = h.id
LEFT JOIN
    (WITH site_filieres AS
         (SELECT b.id,
                 array_to_string(ARRAY_AGG (c.name), ', ', '*') site
          FROM outdoor_course_parent_sites a
          JOIN outdoor_course b ON a.course_id = b.id
          JOIN outdoor_site c ON a.site_id = c.id
          GROUP BY b.id) SELECT a.id,
                                a.site,
                                b.filieres
     FROM site_filieres a
     JOIN
         (WITH filieres AS
              (SELECT c.id,
                      array_to_string(ARRAY_AGG (c.name), ', ', '*') site
               FROM outdoor_course_parent_sites a
               JOIN outdoor_course b ON a.course_id = b.id
               JOIN outdoor_site c ON a.site_id = c.id
               GROUP BY c.id) SELECT a.id,
                                     a.site,
                                     b.filieres
          FROM filieres a
          JOIN
              (SELECT a.id,
                      array_to_string(ARRAY_AGG (c.name), ', ', '*') filieres
               FROM outdoor_site a
               JOIN outdoor_practice b ON a.practice_id = b.id
               JOIN outdoor_sector c ON b.sector_id = c.id
               GROUP BY a.id) b ON a.id = b.id) b ON a.site = b.site) i ON a.id = i.id
WHERE ST_AsText(ST_CollectionExtract(a.geom, 3)) != 'MULTIPOLYGON EMPTY';


CREATE VIEW {{ schema_geotrek }}.v_outdoor_course_line AS
SELECT a.id,
       b.name AS "Structure",
       c.zoning_city AS "City",
       d.zoning_district AS "District",
       {% for lang in MODELTRANSLATIONS %}
        a.name_{{ lang }} AS "Name {{lang}}",
       {% endfor %}
       g.site AS "Sites",
       i.filieres AS "Sectors",
       h.pratique AS "Practice",
       {% for lang in MODELTRANSLATIONS %}
        a.ratings_description AS "Ratings description",
       {% endfor %}
       e.name AS "Type",
       {% for lang in MODELTRANSLATIONS %}
        a.description_{{ lang }} AS "Description {{ lang }}",
       {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.advice AS "Advice",
        {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.gear_{{ lang }} AS "Gear {{ lang }}",
       {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.equipment_{{ lang }} AS "Equipment {{ lang }}",
       {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.accessibility AS "Accessibility {{ lang }}",
       {% endfor %}
       CASE
           WHEN a.height IS NOT NULL THEN concat(a.height, ' m')
           ELSE NULL
       END AS "Height",
       a.duration AS "Duration",
       a.eid AS "External id",
       {% for lang in MODELTRANSLATIONS %}
           CASE
               WHEN a.published_{{ lang }} IS FALSE THEN 'No'
               WHEN a.published_{{ lang }} IS TRUE THEN 'Yes'
           END AS "Published {{ lang }}",
       {% endfor %}
       concat ('→ ', a.length::numeric(10, 1),' m (↝', st_length(geom_3d)::numeric(10, 1),' m)') AS "Humanize length",
       a.length AS "Length",
       st_length(geom_3d) AS "Length 3d",
       CASE
           WHEN ascent > 0 THEN concat (descent,'m +',ascent,'m (',slope::numeric(10, 1),')')
           WHEN ascent < 0 THEN concat (descent,'m -',ascent,'m (',slope::numeric(10, 1),')')
       END AS "Slope",
       a.min_elevation
       CONCAT (a.min_elevation, 'm') AS "Minimum elevation",
       COCANT (a.max_elevation, 'm') AS "Maximum elevation",
       a.date_insert AS "Insertion date",
       a.date_update AS "Update date",
       ST_CollectionExtract(a.geom, 1) AS geom
FROM outdoor_course a
LEFT JOIN authent_structure b ON a.structure_id = b.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name), ', ', '*') zoning_city,
            a.id
     FROM
         outdoor_course a
     JOIN zoning_city b ON ST_INTERSECTS (st_pointonsurface(a.geom), b.geom)
     GROUP BY a.id) c ON a.id = c.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name), ', ', '*') zoning_district,
            a.id
     FROM
         outdoor_course a
     JOIN zoning_district b ON ST_INTERSECTS (st_pointonsurface(a.geom), b.geom)
     GROUP BY a.id) d ON a.id = d.id 
LEFT JOIN outdoor_coursetype e ON a.type_id = e.id
LEFT JOIN
    (SELECT b.id,
            array_to_string(ARRAY_AGG (c.name), ', ', '*') site
     FROM outdoor_course_parent_sites a
     JOIN outdoor_course b ON a.course_id = b.id
     JOIN outdoor_site c ON a.site_id = c.id
     GROUP BY b.id) g ON a.id = g.id
LEFT JOIN
    (WITH site_pratique AS
         (SELECT b.id,
                 array_to_string(ARRAY_AGG (c.name), ', ', '*') site
          FROM outdoor_course_parent_sites a
          JOIN outdoor_course b ON a.course_id = b.id
          JOIN outdoor_site c ON a.site_id = c.id
          GROUP BY b.id) SELECT a.id,
                                a.site,
                                b.pratique
     FROM site_pratique a
     JOIN
         (WITH pratique AS
              (SELECT c.id,
                      array_to_string(ARRAY_AGG (c.name), ', ', '*') site
               FROM outdoor_course_parent_sites a
               JOIN outdoor_course b ON a.course_id = b.id
               JOIN outdoor_site c ON a.site_id = c.id
               GROUP BY c.id) SELECT a.id,
                                     a.site,
                                     b.pratique
          FROM pratique a
          JOIN
              (SELECT a.id,
                      array_to_string(ARRAY_AGG (b.name), ', ', '*') pratique
               FROM outdoor_site a
               JOIN outdoor_practice b ON a.practice_id = b.id
               GROUP BY a.id) b ON a.id = b.id) b ON a.site= b.site) h ON a.id = h.id
LEFT JOIN
    (WITH site_filieres AS
         (SELECT b.id,
                 array_to_string(ARRAY_AGG (c.name), ', ', '*') site
          FROM outdoor_course_parent_sites a
          JOIN outdoor_course b ON a.course_id = b.id
          JOIN outdoor_site c ON a.site_id = c.id
          GROUP BY b.id) SELECT a.id,
                                a.site,
                                b.filieres
     FROM site_filieres a
     JOIN
         (WITH filieres AS
              (SELECT c.id,
                      array_to_string(ARRAY_AGG (c.name), ', ', '*') site
               FROM outdoor_course_parent_sites a
               JOIN outdoor_course b ON a.course_id = b.id
               JOIN outdoor_site c ON a.site_id = c.id
               GROUP BY c.id) SELECT a.id,
                                     a.site,
                                     b.filieres
          FROM filieres a
          JOIN
              (SELECT a.id,
                      array_to_string(ARRAY_AGG (c.name), ', ', '*') filieres
               FROM outdoor_site a
               JOIN outdoor_practice b ON a.practice_id = b.id
               JOIN outdoor_sector c ON b.sector_id = c.id
               GROUP BY a.id) b ON a.id = b.id) b ON a.site = b.site) i ON a.id = i.id
WHERE ST_AsText(ST_CollectionExtract(a.geom, 2)) != 'MULTILINESTRING EMPTY'
   ;


-- Sites outdoor

CREATE VIEW {{ schema_geotrek }}.v_outdoor_site_point AS
SELECT a.id,
       b.name AS "Structure",
       c.zoning_city AS "City",
       d.zoning_district AS "District",
       {% for lang in MODELTRANSLATIONS %}
        a.name AS "Name",
       {% endfor %}
       n.enfants AS "Children",
       o.parents AS "Parents",
       p.filieres AS "Sectors",
       f.name AS "Practice",
       m."Classe",
       m."Caractère vertical",
       m."Caractère aquatique",
       m."Engagement / envergure",
       m."Niveau",
       m."Cotation",
       m."Cotation globale",
       m."Engagement / éloignement",
       e.name AS "Type",
       {% for lang in MODELTRANSLATIONS %}
        description_teaser_{{ lang }} AS "Description teaser {{ lang }}",
       {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.ambiance_{{ lang }} AS "Ambiance {{ lang }}",
       {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.description_{{ lang }} AS "Description {{ lang }}",
       {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.advice_{{ lang }} AS "Advice {{ lang }}",
       {% enfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.accessibility_{{ lang }} AS "Accessibility {{ lang }}",
       {% enfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.period_{{ lang }} AS "Period {{ lang }}",
       {% endfor %}
       a.orientation AS "Orientation",
       a.wind AS "Wind",
       k.etiquettes AS "Label",
       g.lieux_renseignement AS "Information desk",
       i.url AS "Web link",
       j.portail AS "Portal",
       h.name AS "Source",
       l.gestionnaire AS "Manager",
       a.eid AS "External ID",
       {% for lang in MODELTRANSLATIONS %}
           CASE
               WHEN a.published_{{ lang }} IS FALSE THEN 'No'
               WHEN a.published_{{ lang }} IS TRUE THEN 'Yes'
           END AS "Published {{ lang }}",
       {% enfor %}
       CONCAT (a.min_elevation, 'm') AS "Minimum elevation",
       CONCAT (a.max_elevation, 'm') AS "Maximum elevation",
       a.date_insert AS "Insertion date",
       a.date_update AS "Update date",
       ST_CollectionExtract(a.geom, 1) AS geom
FROM public.outdoor_site a
LEFT JOIN authent_structure b ON a.structure_id = b.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name), ', ', '*') zoning_city,
            a.id
     FROM
         outdoor_site a
     JOIN zoning_city b ON ST_INTERSECTS (st_pointonsurface(a.geom), b.geom)
     GROUP BY a.id) c ON a.id = c.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name), ', ', '*') zoning_district,
            a.id
     FROM
         outdoor_site a
     JOIN zoning_district b ON ST_INTERSECTS (st_pointonsurface(a.geom), b.geom)
     GROUP BY a.id) d ON a.id = d.id 
LEFT JOIN outdoor_sitetype e ON a.type_id = e.id
LEFT JOIN outdoor_practice f ON a.practice_id = f.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name), ', ', '*') lieux_renseignement,
            c.id
     FROM outdoor_site_information_desks a
     JOIN tourism_informationdesk b ON a.informationdesk_id =b.id
     JOIN outdoor_site c ON a.site_id = c.id
     GROUP BY c.id) g ON a.id = g.id
LEFT JOIN
    (SELECT a.name,
            c.id
     FROM common_recordsource a
     JOIN outdoor_site_source b ON a.id = b.recordsource_id
     JOIN outdoor_site c ON b.site_id = c.id) h ON a.id = h.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.url), ', ', '*') url,
            d.id
     FROM outdoor_site_web_links a
     JOIN trekking_weblink b ON a.weblink_id = b.id
     JOIN trekking_weblinkcategory c ON b.category_id = c.id
     JOIN outdoor_site d ON d.id = a.site_id
     GROUP BY d.id) i ON a.id = i.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name), ', ', '*') portail,
            c.id
     FROM outdoor_site_portal a
     JOIN common_targetportal b ON a.targetportal_id =b.id
     JOIN outdoor_site c ON a.site_id = c.id
     GROUP BY c.id) j ON a.id = j.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (c.name), ', ', '*') etiquettes,
            d.id
     FROM outdoor_site_labels a
     JOIN trekking_trek_labels b ON a.label_id = b.id
     JOIN common_label c ON b.label_id = c.id
     JOIN outdoor_site d ON a.site_id = d.id
     GROUP BY d.id) k ON a.id = k.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.organism), ', ', '*') gestionnaire,
            c.id
     FROM outdoor_site_managers a
     JOIN common_organism b ON a.organism_id =b.id
     JOIN outdoor_site c ON a.site_id = c.id
     GROUP BY c.id) l ON a.id = l.id
LEFT JOIN
    (WITH rating AS
         (SELECT d.id,
                 CASE
                     WHEN b.name = 'Classe' THEN a.name
                     ELSE NULL
                 END AS "Classe",
                 CASE
                     WHEN b.name = 'Caractère vertical' THEN a.name
                     ELSE NULL
                 END AS "Caractère vertical",
                 CASE
                     WHEN b.name = 'Caractère aquatique' THEN a.name
                     ELSE NULL
                 END AS "Caractère aquatique",
                 CASE
                     WHEN b.name = 'Engagement / envergure' THEN a.name
                     ELSE NULL
                 END AS "Engagement / envergure",
                 CASE
                     WHEN b.name = 'Niveau' THEN a.name
                     ELSE NULL
                 END AS "Niveau",
                 CASE
                     WHEN b.name = 'Cotation' THEN a.name
                     ELSE NULL
                 END AS "Cotation",
                 CASE
                     WHEN b.name = 'Cotation globale' THEN a.name
                     ELSE NULL
                 END AS "Cotation globale",
                 CASE
                     WHEN b.name = 'Engagement / éloignement' THEN a.name
                     ELSE NULL
                 END AS "Engagement / éloignement"
          FROM outdoor_rating a
          JOIN outdoor_ratingscale b ON a.scale_id = b.id
          JOIN outdoor_site_ratings c ON a.id= c.rating_id
          JOIN outdoor_site d ON c.site_id = d.id) SELECT id,
                                                          array_to_string(ARRAY_AGG ("Classe"), ', ', NULL) "Classe",
                                                          array_to_string(ARRAY_AGG ("Caractère vertical"), ', ', NULL) "Caractère vertical",
                                                          array_to_string(ARRAY_AGG ("Caractère aquatique"), ', ', NULL) "Caractère aquatique",
                                                          array_to_string(ARRAY_AGG ("Engagement / envergure"), ', ', NULL) "Engagement / envergure",
                                                          array_to_string(ARRAY_AGG ("Niveau"), ', ', NULL) "Niveau",
                                                          array_to_string(ARRAY_AGG ("Cotation"), ', ', NULL) "Cotation",
                                                          array_to_string(ARRAY_AGG ("Cotation globale"), ', ', NULL) "Cotation globale",
                                                          array_to_string(ARRAY_AGG ("Engagement / éloignement"), ', ', NULL) "Engagement / éloignement"
     FROM rating
     GROUP BY id) m ON a.id = m.id
LEFT JOIN
    (SELECT parent_id,
            array_to_string(ARRAY_AGG (name), ', ', '*') enfants
     FROM public.outdoor_site
     WHERE parent_id IS NOT NULL
     GROUP BY parent_id) n ON a.id = n.parent_id
LEFT JOIN
    (SELECT b.id,
            array_to_string(ARRAY_AGG (a.name), ', ', '*') parents
     FROM outdoor_site a
     JOIN outdoor_site b ON a.id = b.parent_id
     GROUP BY b.id) o ON a.id = o.id
LEFT JOIN
    (SELECT a.id,
            array_to_string(ARRAY_AGG (c.name), ', ', '*') filieres
     FROM outdoor_site a
     JOIN outdoor_practice b ON a.practice_id = b.id
     JOIN outdoor_sector c ON b.sector_id = c.id
     GROUP BY a.id) p ON a.id = p.id
WHERE ST_AsText(ST_CollectionExtract(a.geom, 1)) != 'MULTIPOINT EMPTY'
  --  AND d.name != 'Pyrénées' 
  ;


CREATE VIEW {{ schema_geotrek }}.v_outdoor_site_line AS
SELECT a.id,
       b.name AS "Structure",
       c.zoning_city AS "City",
       d.zoning_district AS "District",
       {% for lang in MODELTRANSLATIONS %}
        a.name AS "Name",
       {% endfor %}
       n.enfants AS "Children",
       o.parents AS "Parents",
       p.filieres AS "Sectors",
       f.name AS "Practice",
       m."Classe",
       m."Caractère vertical",
       m."Caractère aquatique",
       m."Engagement / envergure",
       m."Niveau",
       m."Cotation",
       m."Cotation globale",
       m."Engagement / éloignement",
       e.name AS "Type",
       {% for lang in MODELTRANSLATIONS %}
        description_teaser_{{ lang }} AS "Description teaser {{ lang }}",
       {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.ambiance_{{ lang }} AS "Ambiance {{ lang }}",
       {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.description_{{ lang }} AS "Description {{ lang }}",
       {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.advice_{{ lang }} AS "Advice {{ lang }}",
       {% enfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.accessibility_{{ lang }} AS "Accessibility {{ lang }}",
       {% enfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.period_{{ lang }} AS "Period {{ lang }}",
       {% endfor %}
       a.orientation AS "Orientation",
       a.wind AS "Wind",
       k.etiquettes AS "Label",
       g.lieux_renseignement AS "Information desk",
       i.url AS "Web link",
       j.portail AS "Portal",
       h.name AS "Source",
       l.gestionnaire AS "Manager",
       a.eid AS "External ID",
       {% for lang in MODELTRANSLATIONS %}
           CASE
               WHEN a.published_{{ lang }} IS FALSE THEN 'No'
               WHEN a.published_{{ lang }} IS TRUE THEN 'Yes'
           END AS "Published {{ lang }}",
       {% enfor %}
       CONCAT (a.min_elevation, 'm') AS "Minimum elevation",
       CONCAT (a.max_elevation, 'm') AS "Maximum elevation",
       a.date_insert AS "Insertion date",
       a.date_update AS "Update date",
       ST_CollectionExtract(a.geom, 1) AS geom
FROM public.outdoor_site a
LEFT JOIN authent_structure b ON a.structure_id = b.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name), ', ', '*') zoning_city,
            a.id
     FROM
         outdoor_site a
     JOIN zoning_city b ON ST_INTERSECTS (st_pointonsurface(a.geom), b.geom)
     GROUP BY a.id) c ON a.id = c.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name), ', ', '*') zoning_district,
            a.id
     FROM
         outdoor_site a
     JOIN zoning_district b ON ST_INTERSECTS (st_pointonsurface(a.geom), b.geom)
     GROUP BY a.id) d ON a.id = d.id 
LEFT JOIN outdoor_sitetype e ON a.type_id = e.id
LEFT JOIN outdoor_practice f ON a.practice_id = f.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name), ', ', '*') lieux_renseignement,
            c.id
     FROM outdoor_site_information_desks a
     JOIN tourism_informationdesk b ON a.informationdesk_id =b.id
     JOIN outdoor_site c ON a.site_id = c.id
     GROUP BY c.id) g ON a.id = g.id
LEFT JOIN
    (SELECT a.name,
            c.id
     FROM common_recordsource a
     JOIN outdoor_site_source b ON a.id = b.recordsource_id
     JOIN outdoor_site c ON b.site_id = c.id) h ON a.id = h.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.url), ', ', '*') url,
            d.id
     FROM outdoor_site_web_links a
     JOIN trekking_weblink b ON a.weblink_id = b.id
     JOIN trekking_weblinkcategory c ON b.category_id = c.id
     JOIN outdoor_site d ON d.id = a.site_id
     GROUP BY d.id) i ON a.id = i.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name), ', ', '*') portail,
            c.id
     FROM outdoor_site_portal a
     JOIN common_targetportal b ON a.targetportal_id =b.id
     JOIN outdoor_site c ON a.site_id = c.id
     GROUP BY c.id) j ON a.id = j.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (c.name), ', ', '*') etiquettes,
            d.id
     FROM outdoor_site_labels a
     JOIN trekking_trek_labels b ON a.label_id = b.id
     JOIN common_label c ON b.label_id = c.id
     JOIN outdoor_site d ON a.site_id = d.id
     GROUP BY d.id) k ON a.id = k.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.organism), ', ', '*') gestionnaire,
            c.id
     FROM outdoor_site_managers a
     JOIN common_organism b ON a.organism_id =b.id
     JOIN outdoor_site c ON a.site_id = c.id
     GROUP BY c.id) l ON a.id = l.id
LEFT JOIN
    (WITH rating AS
         (SELECT d.id,
                 CASE
                     WHEN b.name = 'Classe' THEN a.name
                     ELSE NULL
                 END AS "Classe",
                 CASE
                     WHEN b.name = 'Caractère vertical' THEN a.name
                     ELSE NULL
                 END AS "Caractère vertical",
                 CASE
                     WHEN b.name = 'Caractère aquatique' THEN a.name
                     ELSE NULL
                 END AS "Caractère aquatique",
                 CASE
                     WHEN b.name = 'Engagement / envergure' THEN a.name
                     ELSE NULL
                 END AS "Engagement / envergure",
                 CASE
                     WHEN b.name = 'Niveau' THEN a.name
                     ELSE NULL
                 END AS "Niveau",
                 CASE
                     WHEN b.name = 'Cotation' THEN a.name
                     ELSE NULL
                 END AS "Cotation",
                 CASE
                     WHEN b.name = 'Cotation globale' THEN a.name
                     ELSE NULL
                 END AS "Cotation globale",
                 CASE
                     WHEN b.name = 'Engagement / éloignement' THEN a.name
                     ELSE NULL
                 END AS "Engagement / éloignement"
          FROM outdoor_rating a
          JOIN outdoor_ratingscale b ON a.scale_id = b.id
          JOIN outdoor_site_ratings c ON a.id= c.rating_id
          JOIN outdoor_site d ON c.site_id = d.id) SELECT id,
                                                          array_to_string(ARRAY_AGG ("Classe"), ', ', NULL) "Classe",
                                                          array_to_string(ARRAY_AGG ("Caractère vertical"), ', ', NULL) "Caractère vertical",
                                                          array_to_string(ARRAY_AGG ("Caractère aquatique"), ', ', NULL) "Caractère aquatique",
                                                          array_to_string(ARRAY_AGG ("Engagement / envergure"), ', ', NULL) "Engagement / envergure",
                                                          array_to_string(ARRAY_AGG ("Niveau"), ', ', NULL) "Niveau",
                                                          array_to_string(ARRAY_AGG ("Cotation"), ', ', NULL) "Cotation",
                                                          array_to_string(ARRAY_AGG ("Cotation globale"), ', ', NULL) "Cotation globale",
                                                          array_to_string(ARRAY_AGG ("Engagement / éloignement"), ', ', NULL) "Engagement / éloignement"
     FROM rating
     GROUP BY id) m ON a.id = m.id
LEFT JOIN
    (SELECT parent_id,
            array_to_string(ARRAY_AGG (name), ', ', '*') enfants
     FROM public.outdoor_site
     WHERE parent_id IS NOT NULL
     GROUP BY parent_id) n ON a.id = n.parent_id
LEFT JOIN
    (SELECT b.id,
            array_to_string(ARRAY_AGG (a.name), ', ', '*') parents
     FROM outdoor_site a
     JOIN outdoor_site b ON a.id = b.parent_id
     GROUP BY b.id) o ON a.id = o.id
LEFT JOIN
    (SELECT a.id,
            array_to_string(ARRAY_AGG (c.name), ', ', '*') filieres
     FROM outdoor_site a
     JOIN outdoor_practice b ON a.practice_id = b.id
     JOIN outdoor_sector c ON b.sector_id = c.id
     GROUP BY a.id) p ON a.id = p.id
WHERE ST_AsText(ST_CollectionExtract(a.geom, 2)) != 'MULTILINESTRING EMPTY'
  --  AND d.name != 'Pyrénées' 
  ;


CREATE VIEW {{ schema_geotrek }}.v_outdoor_site_polygon AS
SELECT a.id,
       b.name AS "Structure",
       c.zoning_city AS "City",
       d.zoning_district AS "District",
       {% for lang in MODELTRANSLATIONS %}
        a.name AS "Name",
       {% endfor %}
       n.enfants AS "Children",
       o.parents AS "Parents",
       p.filieres AS "Sectors",
       f.name AS "Practice",
       m."Classe",
       m."Caractère vertical",
       m."Caractère aquatique",
       m."Engagement / envergure",
       m."Niveau",
       m."Cotation",
       m."Cotation globale",
       m."Engagement / éloignement",
       e.name AS "Type",
       {% for lang in MODELTRANSLATIONS %}
        description_teaser_{{ lang }} AS "Description teaser {{ lang }}",
       {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.ambiance_{{ lang }} AS "Ambiance {{ lang }}",
       {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.description_{{ lang }} AS "Description {{ lang }}",
       {% endfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.advice_{{ lang }} AS "Advice {{ lang }}",
       {% enfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.accessibility_{{ lang }} AS "Accessibility {{ lang }}",
       {% enfor %}
       {% for lang in MODELTRANSLATIONS %}
        a.period_{{ lang }} AS "Period {{ lang }}",
       {% endfor %}
       a.orientation AS "Orientation",
       a.wind AS "Wind",
       k.etiquettes AS "Label",
       g.lieux_renseignement AS "Information desk",
       i.url AS "Web link",
       j.portail AS "Portal",
       h.name AS "Source",
       l.gestionnaire AS "Manager",
       a.eid AS "External ID",
       {% for lang in MODELTRANSLATIONS %}
           CASE
               WHEN a.published_{{ lang }} IS FALSE THEN 'No'
               WHEN a.published_{{ lang }} IS TRUE THEN 'Yes'
           END AS "Published {{ lang }}",
       {% enfor %}
       CONCAT (a.min_elevation, 'm') AS "Minimum elevation",
       CONCAT (a.max_elevation, 'm') AS "Maximum elevation",
       a.date_insert AS "Insertion date",
       a.date_update AS "Update date",
       ST_CollectionExtract(a.geom, 1) AS geom
FROM public.outdoor_site a
LEFT JOIN authent_structure b ON a.structure_id = b.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name), ', ', '*') zoning_city,
            a.id
     FROM
         outdoor_site a
     JOIN zoning_city b ON ST_INTERSECTS (st_pointonsurface(a.geom), b.geom)
     GROUP BY a.id) c ON a.id = c.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name), ', ', '*') zoning_district,
            a.id
     FROM
         outdoor_site a
     JOIN zoning_district b ON ST_INTERSECTS (st_pointonsurface(a.geom), b.geom)
     GROUP BY a.id) d ON a.id = d.id 
LEFT JOIN outdoor_sitetype e ON a.type_id = e.id
LEFT JOIN outdoor_practice f ON a.practice_id = f.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name), ', ', '*') lieux_renseignement,
            c.id
     FROM outdoor_site_information_desks a
     JOIN tourism_informationdesk b ON a.informationdesk_id =b.id
     JOIN outdoor_site c ON a.site_id = c.id
     GROUP BY c.id) g ON a.id = g.id
LEFT JOIN
    (SELECT a.name,
            c.id
     FROM common_recordsource a
     JOIN outdoor_site_source b ON a.id = b.recordsource_id
     JOIN outdoor_site c ON b.site_id = c.id) h ON a.id = h.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.url), ', ', '*') url,
            d.id
     FROM outdoor_site_web_links a
     JOIN trekking_weblink b ON a.weblink_id = b.id
     JOIN trekking_weblinkcategory c ON b.category_id = c.id
     JOIN outdoor_site d ON d.id = a.site_id
     GROUP BY d.id) i ON a.id = i.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.name), ', ', '*') portail,
            c.id
     FROM outdoor_site_portal a
     JOIN common_targetportal b ON a.targetportal_id =b.id
     JOIN outdoor_site c ON a.site_id = c.id
     GROUP BY c.id) j ON a.id = j.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (c.name), ', ', '*') etiquettes,
            d.id
     FROM outdoor_site_labels a
     JOIN trekking_trek_labels b ON a.label_id = b.id
     JOIN common_label c ON b.label_id = c.id
     JOIN outdoor_site d ON a.site_id = d.id
     GROUP BY d.id) k ON a.id = k.id
LEFT JOIN
    (SELECT array_to_string(ARRAY_AGG (b.organism), ', ', '*') gestionnaire,
            c.id
     FROM outdoor_site_managers a
     JOIN common_organism b ON a.organism_id =b.id
     JOIN outdoor_site c ON a.site_id = c.id
     GROUP BY c.id) l ON a.id = l.id
LEFT JOIN
    (WITH rating AS
         (SELECT d.id,
                 CASE
                     WHEN b.name = 'Classe' THEN a.name
                     ELSE NULL
                 END AS "Classe",
                 CASE
                     WHEN b.name = 'Caractère vertical' THEN a.name
                     ELSE NULL
                 END AS "Caractère vertical",
                 CASE
                     WHEN b.name = 'Caractère aquatique' THEN a.name
                     ELSE NULL
                 END AS "Caractère aquatique",
                 CASE
                     WHEN b.name = 'Engagement / envergure' THEN a.name
                     ELSE NULL
                 END AS "Engagement / envergure",
                 CASE
                     WHEN b.name = 'Niveau' THEN a.name
                     ELSE NULL
                 END AS "Niveau",
                 CASE
                     WHEN b.name = 'Cotation' THEN a.name
                     ELSE NULL
                 END AS "Cotation",
                 CASE
                     WHEN b.name = 'Cotation globale' THEN a.name
                     ELSE NULL
                 END AS "Cotation globale",
                 CASE
                     WHEN b.name = 'Engagement / éloignement' THEN a.name
                     ELSE NULL
                 END AS "Engagement / éloignement"
          FROM outdoor_rating a
          JOIN outdoor_ratingscale b ON a.scale_id = b.id
          JOIN outdoor_site_ratings c ON a.id= c.rating_id
          JOIN outdoor_site d ON c.site_id = d.id) SELECT id,
                                                          array_to_string(ARRAY_AGG ("Classe"), ', ', NULL) "Classe",
                                                          array_to_string(ARRAY_AGG ("Caractère vertical"), ', ', NULL) "Caractère vertical",
                                                          array_to_string(ARRAY_AGG ("Caractère aquatique"), ', ', NULL) "Caractère aquatique",
                                                          array_to_string(ARRAY_AGG ("Engagement / envergure"), ', ', NULL) "Engagement / envergure",
                                                          array_to_string(ARRAY_AGG ("Niveau"), ', ', NULL) "Niveau",
                                                          array_to_string(ARRAY_AGG ("Cotation"), ', ', NULL) "Cotation",
                                                          array_to_string(ARRAY_AGG ("Cotation globale"), ', ', NULL) "Cotation globale",
                                                          array_to_string(ARRAY_AGG ("Engagement / éloignement"), ', ', NULL) "Engagement / éloignement"
     FROM rating
     GROUP BY id) m ON a.id = m.id
LEFT JOIN
    (SELECT parent_id,
            array_to_string(ARRAY_AGG (name), ', ', '*') enfants
     FROM public.outdoor_site
     WHERE parent_id IS NOT NULL
     GROUP BY parent_id) n ON a.id = n.parent_id
LEFT JOIN
    (SELECT b.id,
            array_to_string(ARRAY_AGG (a.name), ', ', '*') parents
     FROM outdoor_site a
     JOIN outdoor_site b ON a.id = b.parent_id
     GROUP BY b.id) o ON a.id = o.id
LEFT JOIN
    (SELECT a.id,
            array_to_string(ARRAY_AGG (c.name), ', ', '*') filieres
     FROM outdoor_site a
     JOIN outdoor_practice b ON a.practice_id = b.id
     JOIN outdoor_sector c ON b.sector_id = c.id
     GROUP BY a.id) p ON a.id = p.id
WHERE ST_AsText(ST_CollectionExtract(a.geom, 3)) != 'MULTIPOLYGON EMPTY'
 --   AND d.name != 'Pyrénées' 
 ;