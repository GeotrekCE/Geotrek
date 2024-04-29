import math
from collections import defaultdict
import json

from django.db import connection
from django.conf import settings
from django.contrib.gis.geos import Point, LineString, MultiLineString, GeometryCollection

import numpy as np
from scipy.sparse.csgraph import dijkstra
from scipy.sparse import csr_matrix

from geotrek.common.utils import sqlfunction
from .models import Path


def path_modifier(path):
    length = 0.0 if math.isnan(path.length) else path.length
    return {"id": path.pk, "length": length}


def get_key_optimizer():
    next_id = iter(range(1, 1000000)).__next__
    mapping = defaultdict(next_id)
    return lambda x: mapping[x]


def graph_edges_nodes_of_qs(qs):
    """
    return a graph on the form:
    nodes {
        coord_point_a {
            coord_point_b: edge_id
        }
    }
    edges {
        edge_id: {
            nodes: [point_a, point_b, ...]
            ** extra settings (length etc.)
        }
    }


    coord_poPathRouterint are tuple of float
    """

    key_modifier = get_key_optimizer()
    value_modifier = path_modifier

    edges = defaultdict(dict)
    nodes = defaultdict(dict)

    for path in qs:
        coords = path.geom.coords
        start_point, end_point = coords[0], coords[-1]
        k_start_point, k_end_point = key_modifier(start_point), key_modifier(end_point)

        v_path = value_modifier(path)
        v_path['nodes_id'] = [k_start_point, k_end_point]
        edge_id = v_path['id']

        nodes[k_start_point][k_end_point] = edge_id
        nodes[k_end_point][k_start_point] = edge_id
        edges[edge_id] = v_path

    return {
        'edges': dict(edges),
        'nodes': dict(nodes),
    }


class PathRouter:
    def __init__(self):
        # To generate IDs for temporary nodes and edges:
        self.id_count = 90000000

        graph = graph_edges_nodes_of_qs(Path.objects.exclude(draft=True))
        self.nodes = graph['nodes']
        self.edges = graph['edges']

    def generate_id(self):
        new_id = self.id_count
        self.id_count += 1
        return new_id

    def get_route(self, steps):
        self.steps = steps
        line_strings = self.compute_list_of_paths()

        multi_line_string = GeometryCollection(line_strings, srid=settings.SRID)
        multi_line_string.transform(settings.API_SRID)
        geojson = json.loads(multi_line_string.geojson)

        return geojson

    def compute_list_of_paths(self):
        all_line_strings = []
        # Compute the shortest path for each pair of adjacent steps
        for i in range(len(self.steps) - 1):
            from_step = self.steps[i]
            to_step = self.steps[i + 1]
            line_strings = self.compute_two_steps_line_strings(from_step, to_step)
            merged_line_string = self.merge_line_strings(line_strings)
            all_line_strings.append(merged_line_string)
        return all_line_strings

    def compute_two_steps_line_strings(self, from_step, to_step):
        from_node_info, to_node_info = self.add_steps_to_graph(from_step, to_step)

        shortest_path = self.get_shortest_path(from_node_info['node_id'],
                                               to_node_info['node_id'])
        line_strings = self.node_list_to_line_strings(shortest_path,
                                                      from_node_info, to_node_info)

        # Restore the graph (remove the steps)
        self.remove_step_from_graph(from_node_info)
        self.remove_step_from_graph(to_node_info)
        return line_strings

    def add_steps_to_graph(self, from_step, to_step):

        def create_point_from_coords(lat, lng):
            point = Point(lng, lat, srid=settings.API_SRID)
            point.transform(settings.SRID)
            return point

        def fill_point_closest_path_info(point):
            # Path and edge info
            point['base_path'] = base_path = Path.closest(point['geom'])
            point['edge_id'] = edge_id = base_path.pk
            point['edge'] = edge = self.edges[edge_id]

            # Nodes linked by this edge
            point['first_node_id'] = edge.get('nodes_id')[0]
            point['last_node_id'] = edge.get('nodes_id')[1]

            # Percentage of the Path this point is on
            base_path_str = f"'{base_path.geom}'"
            point_str = f"'{point['geom'].ewkt}'"
            percent_distance = sqlfunction('SELECT ST_LineLocatePoint',
                                           base_path_str, point_str)[0]
            point['percent_distance'] = percent_distance

        # Create a Point corresponding to each step
        from_point, to_point = {}, {}
        from_point['geom'] = create_point_from_coords(from_step['lat'], from_step['lng'])
        to_point['geom'] = create_point_from_coords(to_step['lat'], to_step['lng'])

        # Get the Path (and corresponding graph edge info) each Point is on
        fill_point_closest_path_info(from_point)
        fill_point_closest_path_info(to_point)

        # If the steps are on the same edge, it's divided into 3 new edges
        if from_point['edge_id'] == to_point['edge_id']:
            from_node_info, to_node_info = self.split_edge_in_three(from_point,
                                                                    to_point)
        # If they are on different edges, both are divided into two new edges
        else:
            from_node_info = self.split_edge_in_two(from_point)
            to_node_info = self.split_edge_in_two(to_point)
        return (from_node_info, to_node_info)

    def remove_step_from_graph(self, node_info):

        # Remove the 2 new edges from the graph:
        # They will have already been deleted if this is the 2nd step and
        # both steps are on the same path
        if self.edges.get(node_info['new_edge1_id']) is not None:
            del self.edges[node_info['new_edge1_id']]
        if self.edges.get(node_info['new_edge2_id']) is not None:
            del self.edges[node_info['new_edge2_id']]

        # Get the 2 nodes this temporary node is linked to
        prev_node = self.nodes.get(node_info['prev_node_id'])
        next_node = self.nodes.get(node_info['next_node_id'])

        # Remove the new node from the graph
        removed_node_id = node_info['node_id']
        del self.nodes[removed_node_id]
        if prev_node is not None:
            # It will have already been deleted if this is the 2nd step and
            # both steps are on the same path
            del prev_node[removed_node_id]
        del next_node[removed_node_id]

    def split_edge_in_two(self, point_info):

        # Get the length of the edges that will be created
        path_length = point_info['base_path'].length
        dist_to_start = path_length * point_info['percent_distance']
        dist_to_end = path_length * (1 - point_info['percent_distance'])

        # Create the new node and edges
        new_node_id = self.generate_id()
        edge1 = {
            'id': self.generate_id(),
            'length': dist_to_start,
            'nodes_id': [point_info['first_node_id'], new_node_id],
        }
        edge2 = {
            'id': self.generate_id(),
            'length': dist_to_end,
            'nodes_id': [new_node_id, point_info['last_node_id']],
        }
        first_node, last_node, new_node = {}, {}, {}
        first_node[new_node_id] = new_node[point_info['first_node_id']] = edge1['id']
        last_node[new_node_id] = new_node[point_info['last_node_id']] = edge2['id']

        # Add them to the graph
        self.edges[edge1['id']] = edge1
        self.edges[edge2['id']] = edge2
        self.nodes[new_node_id] = new_node
        self.extend_dict(self.nodes[point_info['first_node_id']], first_node)
        self.extend_dict(self.nodes[point_info['last_node_id']], last_node)

        new_node_info = {
            'node_id': new_node_id,
            'new_edge1_id': edge1['id'],
            'new_edge2_id': edge2['id'],
            'prev_node_id': point_info['first_node_id'],
            'next_node_id': point_info['last_node_id'],
            'original_egde_id': point_info['edge_id'],
            'percent_of_edge': point_info['percent_distance'],
        }
        return new_node_info

    def split_edge_in_three(self, from_point, to_point):
        # Get the length of the edges that will be created
        path_length = from_point['base_path'].length
        start_percent = from_point['percent_distance']
        end_percent = to_point['percent_distance']

        # If we're going backwards relative to the Path direction
        start_percent, end_percent = end_percent, start_percent

        dist_to_start = path_length * start_percent
        dist_to_end = path_length * (1 - end_percent)
        dist_middle = path_length - dist_to_start - dist_to_end

        # Create the new nodes and edges
        new_node_id_1 = self.generate_id()
        new_node_id_2 = self.generate_id()
        edge1 = {
            'id': self.generate_id(),
            'length': dist_to_start,
            'nodes_id': [from_point['first_node_id'], new_node_id_1],
        }
        edge2 = {
            'id': self.generate_id(),
            'length': dist_middle,
            'nodes_id': [new_node_id_1, new_node_id_2],
        }
        edge3 = {
            'id': self.generate_id(),
            'length': dist_to_end,
            'nodes_id': [new_node_id_2, from_point['last_node_id']],
        }

        # Link them together and to the existing nodes
        first_node, last_node, new_node_1, new_node_2 = {}, {}, {}, {}
        first_node[new_node_id_1] = new_node_1[from_point['first_node_id']] = edge1['id']
        new_node_1[new_node_id_2] = new_node_2[new_node_id_1] = edge2['id']
        new_node_2[from_point['last_node_id']] = last_node[new_node_id_2] = edge3['id']

        # Add them to the graph
        self.edges[edge1['id']] = edge1
        self.edges[edge2['id']] = edge2
        self.edges[edge3['id']] = edge3
        self.nodes[new_node_id_1] = new_node_1
        self.nodes[new_node_id_2] = new_node_2
        self.extend_dict(self.nodes[from_point['first_node_id']], first_node)
        self.extend_dict(self.nodes[from_point['last_node_id']], last_node)

        new_node_info_1 = {
            'node_id': new_node_id_1,
            'new_edge1_id': edge1['id'],
            'new_edge2_id': edge2['id'],
            'prev_node_id': from_point['first_node_id'],
            'next_node_id': new_node_id_2,
            'original_egde_id': from_point['edge_id'],
            'percent_of_edge': from_point['percent_distance'],
        }
        new_node_info_2 = {
            'node_id': new_node_id_2,
            'new_edge1_id': edge2['id'],
            'prev_node_id': new_node_id_1,
            'next_node_id': from_point['last_node_id'],
            'new_edge2_id': edge3['id'],
            'original_egde_id': from_point['edge_id'],
            'percent_of_edge': to_point['percent_distance'],
        }
        return new_node_info_1, new_node_info_2

    def extend_dict(self, dict, source):  # TODO: use dict.update?
        for key, value in source.items():
            dict[key] = value

    def get_shortest_path(self, from_node_id, to_node_id):
        cs_graph = self.get_cs_graph()
        matrix = csr_matrix(cs_graph)

        # List of all nodes IDs -> to interprete dijkstra results
        self.nodes_ids = list(self.nodes.keys())

        def get_node_idx_per_id(node_id):
            try:
                return self.nodes_ids.index(node_id)
            except ValueError:
                return None

        def get_node_id_per_idx(node_idx):
            if node_idx >= len(self.nodes_ids):
                return None
            return self.nodes_ids[node_idx]

        from_node_idx = get_node_idx_per_id(from_node_id)
        to_node_idx = get_node_idx_per_id(to_node_id)
        result = dijkstra(matrix, return_predecessors=True, indices=from_node_idx,
                          directed=False)

        # Retrace the path ID by ID, from end to start
        predecessors = result[1]
        current_node_id, current_node_idx = to_node_id, to_node_idx
        path = [current_node_id]
        while current_node_id != from_node_id:
            current_node_idx = predecessors[current_node_idx]
            current_node_id = get_node_id_per_idx(current_node_idx)
            path.append(current_node_id)

        path.reverse()
        return path

    def get_cs_graph(self):

        def get_edge_weight(edge_id):
            edge = self.edges.get(edge_id)
            if edge is None:
                return None
            return edge.get('length')

        array = []
        for key1, value1 in self.nodes.items():
            row = []
            for key2, value2 in self.nodes.items():
                if key1 == key2:
                    # If it's the same node, the weight is 0
                    row.append(0)
                elif key2 in value1.keys():
                    # If the nodes are linked by a single edge, the weight is
                    # the edge length
                    edge_id = self.get_edge_id_by_nodes(value1, value2)
                    edge_weight = get_edge_weight(edge_id)
                    if edge_weight is not None:
                        row.append(edge_weight)
                else:
                    # If the nodes are not directly linked, the weight is 0
                    row.append(0)
            array.append(row)

        return np.array(array)

    def node_list_to_line_strings(self, node_list, from_node_info, to_node_info):
        line_strings = []
        # Get a LineString for each pair of adjacent nodes in the path
        for i in range(len(node_list) - 1):
            # Get the id of the edge corresponding to these nodes
            node1 = self.nodes[node_list[i]]
            node2 = self.nodes[node_list[i + 1]]
            edge_id = self.get_edge_id_by_nodes(node1, node2)

            # If this pair of nodes requires to go backwards relative to a
            # Path direction (i.e. the edge 2nd node is the 1st of this pair)
            backwards = False
            if self.edges[edge_id]['nodes_id'][1] == node_list[i]:
                backwards = True

            # If it's the first or last edge of this subpath (it can be both!),
            # then the edge is temporary (i.e. created because of a step)
            if i == 0 or i == len(node_list) - 2:
                # Start and end percentages of the line substring to be created
                start_fraction = 0
                end_fraction = 1
                if backwards:
                    start_fraction, end_fraction = end_fraction, start_fraction

                if i == 0:
                    original_path = Path.objects.get(pk=from_node_info['original_egde_id'])
                    start_fraction = from_node_info['percent_of_edge']
                if i == len(node_list) - 2:
                    original_path = Path.objects.get(pk=to_node_info['original_egde_id'])
                    end_fraction = to_node_info['percent_of_edge']

                line_substring = self.create_line_substring(
                    original_path.geom,
                    start_fraction,
                    end_fraction
                )
                line_strings.append(line_substring)

            # If it's a real edge (i.e. it corresponds to a whole path),
            # we use its LineString
            else:
                path = Path.objects.get(pk=edge_id)
                line_strings.append(path.geom)

        return line_strings

    def get_edge_id_by_nodes(self, node1, node2):
        for value in node1.values():
            if value in node2.values():
                return value
        return None

    def create_line_substring(self, geometry, start_fraction, end_fraction):
        sql = """
        SELECT ST_AsText(ST_SmartLineSubstring('{}'::geometry, {}, {}))
        """.format(geometry, start_fraction, end_fraction)

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
        rounded_line_strings = [
            self.round_line_string_coordinates(ls) for ls in line_strings
        ]
        multi_line_string = MultiLineString(rounded_line_strings, srid=settings.SRID)
        return multi_line_string.merged

    def round_line_string_coordinates(self, line_string):
        # TODO: see which precision level is best
        coords = line_string.coords
        new_coords = [[round(nb, 4) for nb in pt_coord] for pt_coord in coords]
        new_line_string = LineString(new_coords, srid=line_string.srid)
        return new_line_string
