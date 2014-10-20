SELECT set_schema('e_r_evenement_troncon', 'geotrek');
SELECT set_schema('e_t_evenement', 'geotrek');
SELECT set_schema('l_b_confort', 'geotrek');
SELECT set_schema('l_b_enjeu', 'geotrek');
SELECT set_schema('l_b_reseau', 'geotrek');
SELECT set_schema('l_b_source', 'geotrek');
SELECT set_schema('l_b_usage', 'geotrek');
SELECT set_schema('l_r_troncon_reseau', 'geotrek');
SELECT set_schema('l_r_troncon_usage', 'geotrek');
SELECT set_schema('l_t_sentier', 'geotrek');
SELECT set_schema('l_v_sentier', 'geotrek');
SELECT set_schema('l_t_troncon', 'geotrek');

SELECT set_schema_ft('ST_InterpolateAlong(geometry, geometry)', 'geotrek');
SELECT set_schema_ft('ST_Smart_Line_Substring(geometry, float, float)', 'geotrek');
SELECT set_schema_ft('ft_IsBefore(geometry, geometry)', 'geotrek');
SELECT set_schema_ft('ft_IsAfter(geometry, geometry)', 'geotrek');
SELECT set_schema_ft('ft_Smart_MakeLine(geometry[])', 'geotrek');
SELECT set_schema_ft('evenement_latest_updated_d()', 'geotrek');
SELECT set_schema_ft('update_geometry_of_evenement(integer)', 'geotrek');
SELECT set_schema_ft('update_evenement_geom_when_offset_changes()', 'geotrek');
SELECT set_schema_ft('evenement_elevation_iu()', 'geotrek');
SELECT set_schema_ft('evenement_elevation_iu()', 'geotrek');
SELECT set_schema_ft('ft_troncon_interpolate(integer, geometry)', 'geotrek');
SELECT set_schema_ft('ft_evenements_troncons_geometry()', 'geotrek');
SELECT set_schema_ft('ft_evenements_troncons_junction_point_iu()', 'geotrek');
SELECT set_schema_ft('check_path_not_overlap(integer, geometry)', 'geotrek');
SELECT set_schema_ft('update_evenement_geom_when_troncon_changes()', 'geotrek');
SELECT set_schema_ft('elevation_troncon_iu()', 'geotrek');
SELECT set_schema_ft('troncons_related_objects_d()', 'geotrek');
SELECT set_schema_ft('troncon_latest_updated_d()', 'geotrek');
SELECT set_schema_ft('troncons_snap_extremities()', 'geotrek');
SELECT set_schema_ft('troncons_evenement_intersect_split()', 'geotrek');
