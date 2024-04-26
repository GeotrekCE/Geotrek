var Geotrek = Geotrek || {};

Geotrek.TopologyHelper = (function() {

    /**
     * @param idToLayer : callback to obtain a layer object from a pk/id.
     * @param data : computed_path
     */
    function buildTopologyFromComputedPath(idToLayer, data) {

        var layer = L.featureGroup();
        data.geojson.geometries.forEach((geom, i) => {
            var sub_layer = L.geoJson(geom);
            sub_layer.step_idx = i
            layer.addLayer(sub_layer);
        })

        return {
            layer: layer,
            serialized: null
            // TODO serialized: data
        };
    }

    return {
        buildTopologyFromComputedPath: buildTopologyFromComputedPath
    };
})();
