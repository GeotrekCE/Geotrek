var Geotrek = Geotrek || {};

Geotrek.TopologyHelper = (function() {

    /**
     * This static function takes a list of Dijkstra results, and returns
     * a serialized topology, as expected by form widget, as well as a
     * multiline geometry for highlight the result.
     */
    function buildSubTopology(paths, polylines, ll_start, ll_end, offset) {
        var polyline_start = polylines[0]
          , polyline_end = polylines[polylines.length - 1]
          , single_path = paths.length == 1
          , cleanup = true
          , positions = {};

        if (!polyline_start || !polyline_end) {
            console.error("Could not compute distances without polylines.");
            return null;  // TODO: clean-up before give-up ?
        }

        var pk_start = L.GeometryUtil.locateOnLine(polyline_start._map, polyline_start, ll_start),
            pk_end = L.GeometryUtil.locateOnLine(polyline_end._map, polyline_end, ll_end);
        console.debug('Start on layer ' + polyline_start.properties.id + ' ' + pk_start + ' ' + ll_start.toString());
        console.debug('End on layer ' + polyline_end.properties.id + ' ' + pk_end + ' ' + ll_end.toString());

        if (single_path) {
            var path_pk = paths[0],
                lls = polyline_start.getLatLngs();

            single_path_loop = lls[0].equals(lls[lls.length-1]);
            if (single_path_loop)
                cleanup = false;

            if (single_path_loop && Math.abs(pk_end - pk_start) > 0.5) {
                /*
                 *        A
                 *     //=|---+
                 *   +//      |   It is shorter to go through
                 *    \\      |   extremeties than the whole loop
                 *     \\=|---+
                 *        B
                 */
                if (pk_end - pk_start > 0.5) {
                    paths = [path_pk, path_pk];
                    positions[0] = [pk_start, 0.0];
                    positions[1] = [1.0, pk_end];
                }
                else if (pk_end - pk_start < -0.5) {
                    paths = [path_pk, path_pk];
                    positions[0] = [pk_end, 0.0];
                    positions[1] = [1.0, pk_start];
                }
            }
            else {
                /*        A     B
                 *   +----|=====|---->
                 *
                 *        B     A
                 *   +----|=====|---->
                 */
                paths = $.unique(paths);
                positions[0] = [pk_start, pk_end];
            }
        }
        else if (paths.length == 3 && polyline_start == polyline_end) {
            var start_lls = polylines[0].getLatLngs()
              , mid_lls = polylines[1].getLatLngs();
            cleanup = false;
            if (pk_start < pk_end) {
                positions[0] = [pk_start, 0.0];
                if (start_lls[0].equals(mid_lls[0]))
                    positions[1] = [0.0, 1.0];
                else
                    positions[1] = [1.0, 0.0];
                positions[2] = [1.0, pk_end];
            }
            else {
                positions[0] = [pk_start, 1.0];
                if (start_lls[0].equals(mid_lls[0]))
                    positions[1] = [1.0, 0.0];
                else
                    positions[1] = [0.0, 1.0];
                positions[2] = [0.0, pk_end];
            }
        }
        else {
            /*
             * Add first portion of line
             */
            var start_lls = polyline_start.getLatLngs(),
                first_end = start_lls[start_lls.length-1],
                start_on_loop = start_lls[0].equals(first_end);

            if (L.GeometryUtil.startsAtExtremity(polyline_start, polylines[1])) {
                var next_lls = polylines[1].getLatLngs(),
                    next_end = next_lls[next_lls.length-1],
                    share_end = first_end.equals(next_end),
                    two_paths_loop = first_end.equals(next_lls[0]);
                if ((start_on_loop && pk_start > 0.5) ||
                    (share_end && (pk_start + pk_end) >= 1) ||
                    (two_paths_loop && (pk_start - pk_end) > 0)) {
                    /*
                     *       A
                     *    /--|===+    B
                     *  +/       \\+==|---
                     *   \       /
                     *    \-----+
                     *
                     *        A               B
                     *   +----|------><-------|----
                     *
                     *   +----|=====|><=======|----
                     *
                     */
                    positions[0] = [pk_start, 1.0];
                }
                else {
                    /*
                     *        A               B
                     *   <----|------++-------|----
                     *
                     *   <----|=====|++=======|----
                     *
                     */
                    positions[0] = [pk_start, 0.0];
                }
            } else {
                /*
                 *        A               B
                 *   +----|------>+-------|----
                 *
                 *   +----|=====|>+=======|----
                 *
                 */
                positions[0] = [pk_start, 1.0];
            }

            /*
             * Add all intermediary lines
             */
            for (var i=1; i<polylines.length-1; i++) {
                var previous = polylines[i-1],
                    polyline = polylines[i];
                if (L.GeometryUtil.startsAtExtremity(polyline, previous)) {
                    positions[i] = [0.0, 1.0];
                }
                else {
                    positions[i] = [1.0, 0.0];
                }
            }

            /*
             * Add last portion of line
             */
            var end_lls = polyline_end.getLatLngs(),
                last_end = end_lls[end_lls.length-1],
                end_on_loop = end_lls[0].equals(last_end);

            if (L.GeometryUtil.startsAtExtremity(polyline_end, polylines[polylines.length - 2])) {
                var previous_lls = polylines[polylines.length - 2].getLatLngs(),
                    previous_end = previous_lls[previous_lls.length-1],
                    share_end = last_end.equals(previous_end),
                    two_paths_loop = last_end.equals(previous_lls[0]);
                if ((end_on_loop && pk_end > 0.5) ||
                    (share_end && (pk_start + pk_end) >= 1) ||
                    (two_paths_loop && (pk_start - pk_end) <= 0)) {
                    /*
                     *              B
                     *     A    //==|-+
                     *  ---|==+//     |
                     *         \      |
                     *          \-----+
                     *
                     *        A               B
                     *   -----|------><-------|----+
                     *
                     *   -----|======>|+======>---->
                     */
                    positions[polylines.length - 1] = [1.0, pk_end];
                }
                else {
                    /*
                     *        A               B
                     *   -----|------++-------|---->
                     *
                     *   -----|======+|=======>---->
                     */
                    positions[polylines.length - 1] = [0.0, pk_end];
                }
            } else {
                /*
                 *        A               B
                 *   -----|------+<-------|----+
                 *
                 *   -----|=====|+<=======|----+
                 */
                positions[polylines.length - 1] = [1.0, pk_end];
            }
        }

        // Clean-up :
        // We basically remove all points where position is [x,x]
        // This can happen at extremity points...

        if (cleanup) {
            var cleanpaths = [],
                cleanpositions = {};
            for (var i=0; i < paths.length; i++) {
                var path = paths[i];
                if (i in positions) {
                    if (positions[i][0] != positions[i][1] && cleanpaths.indexOf(path) == -1) {
                        cleanpaths.push(path);
                        cleanpositions[i] = positions[i];
                    }
                }
                else {
                    cleanpaths.push(path);
                }
            }
            paths = cleanpaths;
            positions = cleanpositions;
        }

        // Safety warning.
        if (paths.length === 0)
            console.error('Empty topology. Expect problems. (' + JSON.stringify({positions:positions, paths:paths}) + ')');

        return {
            offset: offset,       // Float for offset
            positions: positions, // Positions on paths
            paths: paths          // List of pks
        };
    }

    /**
     * @param topology {Object} with ``offset``, ``positions`` and ``paths`` as returned by buildSubTopology()
     * @param idToLayer {function} callback to obtain layer from id
     * @returns L.multiPolyline
     */
    function buildGeometryFromTopology(topology, idToLayer) {
        var latlngs = [];
        for (var i=0; i < topology.paths.length; i++) {
            var path = topology.paths[i],
                positions = topology.positions[i],
                polyline = idToLayer(path);
            if (positions) {
                latlngs.push(L.GeometryUtil.extract(polyline._map, polyline, positions[0], positions[1]));
            }
            else {
                console.warn('Topology problem: ' + i + ' not in ' + JSON.stringify(topology.positions));
            }
        }
        return L.multiPolyline(latlngs);
    }

    /**
     * @param idToLayer : callback to obtain a layer object from a pk/id.
     * @param data : computed_path
     */
    function buildTopologyFromComputedPath(idToLayer, data) {
        // if (!data.computed_paths) {
        //     return {
        //         layer: null,
        //         serialized: null
        //     }
        // }
        
        //var pathLayer = L.geoJson(geojson, {color:"blue", weight: 10})
        
        var computed_paths = data['computed_paths']
        , edges = data['new_edges']
        , offset = 0.0  // TODO: input for offset
        //, data = []
        console.log("computed_paths", computed_paths)

        console.debug('----');
        console.debug('Topology has ' + computed_paths.length + ' sub-topologies.');
        
        // for (var i = 0; i < computed_paths.length; i++ ) {
            //     var cpath = computed_paths[i],
            //         paths = $.map(edges[i], function(edge) { return edge.id; }),
            //         polylines = $.map(edges[i], function(edge) { return idToLayer(edge.id); });
            
            //     var topo = buildSubTopology(paths,
            //                                 polylines,
            //                                 cpath.from_pop.ll,
            //                                 cpath.to_pop.ll,
            //                                 offset);
            //     if (topo === null) break;
            
            //     data.push(topo);
            //     console.debug('subtopo[' + i + '] : ' + JSON.stringify(topo));
            
            //     // Geometry for each sub-topology
            //     var group_layer = buildGeometryFromTopology(topo, idToLayer);
            //     // group_layer.from_pop = cpath.from_pop;
            //     // group_layer.to_pop = cpath.to_pop;
            //     // group_layer.step_idx = i;
            //     layer.addLayer(group_layer);
            // }

        var geojson = data.geojson
        var layer = L.featureGroup();
        for (var i = 0; i < geojson.length; i++) {
            var latlngs = []
            var lineString = geojson[i]
            for (var j = 0; j < lineString.coordinates.length - 1; j++) {
                var currentCoords = lineString.coordinates[j]
                var nextCoords = lineString.coordinates[j + 1]
                var newCoords = [
                    {
                        lat: currentCoords[1],
                        lng: currentCoords[0],
                    },
                    {
                        lat: nextCoords[1],
                        lng: nextCoords[0],
                    },
                ]
                latlngs.push(newCoords)
            }
            console.log("latlngs", latlngs)
            var group_layer = L.multiPolyline(latlngs);
            group_layer.step_idx = i
            layer.addLayer(group_layer);
        }

        //console.log(pathLayer)
        console.debug('----');

        return {
            layer: layer,
            serialized: null
            //serialized: data
        };
    }

    return {
        buildTopologyFromComputedPath: buildTopologyFromComputedPath
    };
})();
