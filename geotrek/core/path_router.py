import json

from django.db import connection
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, Point, LineString, MultiLineString, GeometryCollection

from geotrek.common.utils import sqlfunction
from .models import Path


class PathRouter:
    def __init__(self):
        self.set_path_network_topology()

    def set_path_network_topology(self):
        """ Builds or updates the paths graph (pgRouting network topology) """
        cursor = connection.cursor()
        query = """
                SELECT
                    pgr_createTopology(
                        'core_path',
                        %s::float,
                        'geom',
                        'id'
                    )
                """
        cursor.execute(query, [settings.PATH_SNAPPING_DISTANCE])
        return ('OK',) == cursor.fetchone()

    def get_route(self, steps):
        """
        Returns the whole route's geojson and topology. Both of them is an array
        with each element being a sub-route from one step to another. The geojson
        geometry's srid corresponds to the frontend's.
        """
        self.steps = steps
        self.steps_topo = [
            {
                'edge_id': step.get('path_id'),
                'fraction': self.get_step_fraction(step)
            }
            for step in steps
        ]
        line_strings, serialized_topology = self.compute_all_steps_routes()
        if line_strings == []:
            return None

        multi_line_string = GeometryCollection(line_strings, srid=settings.SRID)
        multi_line_string.transform(settings.API_SRID)
        geojson = json.loads(multi_line_string.geojson)

        return {'geojson': geojson, 'serialized': serialized_topology}

    def get_step_fraction(self, step):
        """
        For one step on a path, returns its position on the path.
        """
        # Transform the point to the right SRID
        point = Point(step.get('lng'), step.get('lat'), srid=settings.API_SRID)
        point.transform(settings.SRID)
        # Get the closest path
        closest_path = Path.objects.get(pk=step.get('path_id'))
        # Get which fraction of the Path this point is on
        closest_path_geom = f"'{closest_path.geom}'"
        point_geom = f"'{point.ewkt}'"
        fraction_of_distance = sqlfunction('SELECT ST_LineLocatePoint',
                                           closest_path_geom, point_geom)[0]
        return fraction_of_distance

    def compute_all_steps_routes(self):
        """
        Returns the whole route's geometries and topology. Both of them is an array
        with each element being a sub-route from one step to another.
        """
        all_steps_geometries = []  # Each elem is a linestring from one step to another
        all_steps_topologies = []  # Each elem is the topology from one step to another
        # Compute the shortest path for each pair of adjacent steps
        for i in range(len(self.steps_topo) - 1):
            from_step = self.steps_topo[i]
            to_step = self.steps_topo[i + 1]
            # Get the linestrings (segments of paths) between those two steps,
            # then merge them into one
            one_step_geometry, topology = self.get_two_steps_route(from_step, to_step)
            all_steps_topologies.append(topology)
            if one_step_geometry is None:
                return [], []
            all_steps_geometries.append(one_step_geometry)
        return all_steps_geometries, all_steps_topologies

    def get_two_steps_route(self, from_step, to_step):
        """
        Returns the geometry (as a LineString) and the topology of a subroute.
        Parameters:
            from_step: {edge_id: int, fraction: float}
            to_step: {edge_id: int, fraction: float}
        """
        from_edge_id = from_step.get('edge_id')
        to_edge_id = to_step.get('edge_id')

        if from_edge_id == to_edge_id:
            from_fraction = from_step.get('fraction')
            to_fraction = to_step.get('fraction')
            # If both points are on same edge, split it from the 1st to the 2nd
            path_substring = self.create_path_substring(
                from_edge_id,
                from_fraction,
                to_fraction
            )
            line_strings = [path_substring]
            topology = {
                'positions': {'0': [from_fraction, to_fraction]},
                'paths': [from_edge_id],
            }
        else:
            # Compute the shortest path between the two points
            line_strings, topology = self.compute_two_steps_route(from_step, to_step)
            if line_strings == []:
                return None, None

        step_geometry = self.merge_line_strings(line_strings)
        return step_geometry, topology

    def compute_two_steps_route(self, from_step, to_step):
        """
        Computes the geometry (as an array of LineStrings) and the topology of
        a subroute by using pgRouting.
        Parameters:
            from_step: {edge_id: int, fraction: float}
            to_step: {edge_id: int, fraction: float}
        """
        start_edge = from_step.get('edge_id')
        end_edge = to_step.get('edge_id')
        fraction_start = self._fix_fraction(from_step.get('fraction'))
        fraction_end = self._fix_fraction(to_step.get('fraction'))

        query = """
            DO $$
            DECLARE
                max_edge_id integer;
                max_vertex_id integer;

            BEGIN

                SELECT MAX(id) FROM core_path INTO max_edge_id;
                SELECT MAX(vid) FROM (
                    SELECT source AS vid FROM core_path
                    UNION
                    SELECT target AS vid FROM core_path
                ) AS vids INTO max_vertex_id;

                DROP TABLE IF EXISTS temporary_edges_info;
                CREATE TEMPORARY TABLE temporary_edges_info AS
                    -- This info will be added to the A* inner query edges_sql.
                    -- It represents the temporary edges created by adding the start
                    -- and end steps as nodes onto the graph (aka pgr network topology)
                    WITH graph_temporary_edges AS (
                        SELECT
                            core_path.id AS path_id,
                            max_edge_id + index AS edge_id,
                            ST_SmartLineSubstring(
                                core_path.geom,
                                fraction_start,
                                fraction_end
                            ) as edge_geom,
                            CASE
                                WHEN (index % 2) != 0
                                    THEN core_path.source
                                    ELSE max_vertex_id + (index > 2)::int + 1
                                END AS source_id,
                            CASE
                                WHEN (index % 2) = 0
                                    THEN core_path.target
                                    ELSE max_vertex_id + (index > 2)::int + 1
                                END AS target_id,
                            CASE
                                WHEN (index % 2) != 0
                                    THEN ST_StartPoint(geom)
                                    ELSE ST_LineInterpolatePoint(core_path.geom, fraction_start)
                                END AS source_geom,
                            CASE
                                WHEN (index % 2) = 0
                                    THEN ST_EndPoint(geom)
                                    ELSE ST_LineInterpolatePoint(core_path.geom, fraction_end)
                                END AS target_geom
                        FROM (
                            VALUES
                                (1, '{}'::int, 0, '{}'::float),
                                (2, '{}'::int, '{}'::float, 1),
                                (3, '{}'::int, 0, '{}'::float),
                                (4, '{}'::int, '{}'::float, 1)
                        ) AS tmp_edges_info (index, path_id, fraction_start, fraction_end)
                        JOIN core_path ON core_path.id = tmp_edges_info.path_id
                    )
                    SELECT
                        path_id,
                        edge_id AS id,
                        source_id AS source,
                        target_id AS target,
                        ST_Length(edge_geom) AS cost,
                        ST_Length(edge_geom) AS reverse_cost,
                        ST_X(source_geom) AS x1,
                        ST_Y(source_geom) AS y1,
                        ST_X(target_geom) AS x2,
                        ST_Y(target_geom) AS y2,
                        edge_geom as geom
                    FROM graph_temporary_edges;

                DROP TABLE IF EXISTS route;
                CREATE TEMPORARY TABLE route AS
                WITH pgr AS (
                    SELECT
                        pgr.path_seq,
                        pgr.node,
                        (LEAD(pgr.node) OVER (ORDER BY path_seq)) AS next_node,
                        COALESCE(core_path.source, temporary_edges_info.source) as source,
                        COALESCE(core_path.target, temporary_edges_info.target) as target,
                        COALESCE(core_path.geom, temporary_edges_info.geom) as edge_geom,
                        CASE
                            WHEN pgr.edge > max_edge_id
                                THEN temporary_edges_info.path_id
                                ELSE pgr.edge
                            END AS edge
                    FROM
                        pgr_aStar(
                            'SELECT
                                id,
                                source,
                                target,
                                length AS cost,
                                length AS reverse_cost,
                                ST_X(ST_StartPoint(geom)) AS x1,
                                ST_Y(ST_StartPoint(geom)) AS y1,
                                ST_X(ST_EndPoint(geom)) AS x2,
                                ST_Y(ST_EndPoint(geom)) AS y2
                            FROM core_path
                            WHERE draft = false AND visible = true
                            UNION ALL SELECT
                                id, source, target, cost, reverse_cost, x1, y1, x2, y2
                            FROM temporary_edges_info
                            ORDER by id',
                            max_vertex_id + 1, max_vertex_id + 2
                        ) AS pgr
                        LEFT JOIN core_path ON id = pgr.edge
                        LEFT JOIN temporary_edges_info ON temporary_edges_info.id = pgr.edge
                        WHERE edge != -1
                )
                SELECT
                    CASE
                        WHEN source = next_node THEN ST_Reverse(edge_geom)
                        ELSE edge_geom
                        END AS edge_geom,
                    edge,
                    CASE
                        WHEN node = max_vertex_id + 1 THEN '{}'::float
                        WHEN node = source THEN 0
                        ELSE 1  -- node = target
                        END AS fraction_start,
                    CASE
                        WHEN next_node IS NULL THEN '{}'::float
                        WHEN next_node = source THEN 0
                        ELSE 1  -- next_node = target
                        END AS fraction_end
                FROM pgr;

            END $$;

            SELECT
                edge_geom,
                edge,
                fraction_start,
                fraction_end
            FROM route
        """.format(
            start_edge, fraction_start,
            start_edge, fraction_start,
            end_edge, fraction_end,
            end_edge, fraction_end,
            fraction_start, fraction_end
        )

        with connection.cursor() as cursor:
            cursor.execute(query)

            query_result = cursor.fetchall()
            if query_result == []:
                return [], None

            geometries, edge_ids, fraction_starts, fraction_ends = list(zip(*query_result))
            return (
                [
                    # Convert each geometry to a LineString
                    MultiLineString(*[GEOSGeometry(geometry)]).merged
                    for geometry in geometries
                ],
                {
                    'positions': dict([
                        (str(i), [fraction_starts[i], fraction_ends[i]])
                        for i in range(len(fraction_starts))
                    ]),
                    'paths': list(edge_ids),
                }
            )

    def _fix_fraction(self, fraction):
        """ This function is used to fix an issue with pgRouting where a point's
        position on an edge being 0.0 or 1.0 create a routing topology problem.
        See https://github.com/pgRouting/pgrouting/issues/760
        So we create a fake fraction near the vertices of the edge.
        """
        if float(fraction) == 1.0:
            return 0.99999
        elif float(fraction) == 0.0:
            return 0.00001
        return fraction

    def create_path_substring(self, path_id, start_fraction, end_fraction):
        """
        Returns a path's substring for which start_fraction can be bigger than
        end_fraction.
        """
        path = Path.objects.get(pk=path_id)
        sql = """
        SELECT ST_AsText(ST_SmartLineSubstring('{}'::geometry, {}, {}))
        """.format(path.geom, start_fraction, end_fraction)

        cursor = connection.cursor()
        cursor.execute(sql)
        result = cursor.fetchone()[0]

        # Convert the string into an array of arrays of floats
        coords_str = result.split('(')[1].split(')')[0]
        str_points_array = [elem.split(' ') for elem in coords_str.split(',')]
        arr = [[float(nb) for nb in sub_array] for sub_array in str_points_array]

        line_substring = LineString(arr, srid=settings.SRID)
        return line_substring

    def merge_line_strings(self, line_strings):
        multi_line_string = MultiLineString(line_strings, srid=settings.SRID)
        return multi_line_string.merged
