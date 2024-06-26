MapEntity.pathsLayer = function buildPathLayer(options) {
    var options = options || {};
    options.style = L.Util.extend(options.style || {}, window.SETTINGS.map.styles.path);

    var pathsLayer = new L.ObjectsLayer(null, options);

    // Show paths extremities
    if (window.SETTINGS.showExtremities) {
        pathsLayer.on('data:loaded', function (e) {
            pathsLayer.showExtremities(window.SETTINGS.map.paths_line_marker);
        });
    }
    return pathsLayer;
};

$(window).on('entity:map', function (e, data) {
    var map = data.map;
    var loaded_path = false;
    // Show the path layer only if model is not path, and if we are not
    // in an editing widget or when it's not a topology
    var is_form_view = /add|update/.test(data.viewname);
    var is_not_topology = /dive|report|touristiccontent|touristicevent|site|course/.test(data.modelname);
    if (is_not_topology || (!is_form_view && (data.viewname == 'detail' || data.modelname != 'path'))) {

        var pathsLayer = MapEntity.pathsLayer({
            indexing: false,
            style: { clickable: false },
            modelname: 'path',
            no_draft: data.modelname != 'path',
        });
        if (data.viewname == 'detail'){
            pathsLayer.load(window.SETTINGS.urls.path_layer);
            pathsLayer.addTo(map);
        };
        pathsLayer.on('loaded', function () {
            if (pathsLayer._map)
                pathsLayer.bringToBack();
        });

        map.on('layeradd', function (e) {
            // Start ajax loading at last
            url = window.SETTINGS.urls.path_layer

            var options = e.layer.options || {'modelname': 'None'};
            if (! loaded_path){
                if (options.modelname == 'path' && data.viewname != 'detail'){
                    e.layer.load(url + '?_no_draft=true', true);
                    loaded_path = true;
                };

            }

            if (e.layer === pathsLayer) {

                if (!e.layer._map) {
                    return;
                }
                if (e.layer.loading) {
                    e.layer.on('loaded', function () {
                        if (!e.layer._map) {
                            return;
                        }
                        e.layer.bringToBack();
                    });
                }
                else {
                    e.layer.bringToBack();
                }
            }
            else {
                if (e.layer instanceof L.ObjectsLayer) {
                    if (e.layer.loading) {
                        e.layer.on('loaded', function () {
                            if (!e.layer._map) {
                                return;
                            }
                            e.layer.bringToFront();
                        });
                    }
                    else {
                        e.layer.bringToFront();
                    }
                }
            }
        });

        var style = pathsLayer.options.style;
        var nameHTML = '<span style="color: '+ style['color'] + ';">&#9473;</span>&nbsp;' + tr('Paths');
        map.layerscontrol.addOverlay(pathsLayer, nameHTML, tr('Paths'));

        //
        // Print apparence of paths
        $(window).on('detailmap:ready', function (e, data) {
            if ((data.modelname != 'path') &&
                (data.context && data.context.print)) {
                var specified = window.SETTINGS.map.styles.print.path;
                pathsLayer.setStyle(L.Util.extend(pathsLayer.options.style, specified));
            }
        });
    }
});

$(window).on('detailmap:ready', function (e, data) {
    var map = data.map,
        layer = data.layer,
        DETAIL_STYLE = window.SETTINGS.map.styles.detail;

    if (data.context && data.context.print) {
        var specified = window.SETTINGS.map.styles.print[data.modelname];
        DETAIL_STYLE = L.Util.extend(DETAIL_STYLE, specified || {});
    }

    // Show start and end
    layer.eachLayer(function (layer) {
        if (layer instanceof L.MultiPolyline)
            return;
        if (layer instanceof L.Polygon)
            return;
        if (typeof layer.getLatLngs != 'function')  // points
            return;

        // Show start and end markers (similar to edition)
        var _iconUrl = window.SETTINGS.urls.static + "core/images/marker-";
        L.marker(layer.getLatLngs()[0], {
            clickable: false,
            icon: new L.Icon.Default({iconUrl: _iconUrl + "source.png"})
        }).addTo(map);
        L.marker(layer.getLatLngs().slice(-1)[0], {
            clickable: false,
            icon: new L.Icon.Default({iconUrl: _iconUrl + "target.png"})
        }).addTo(map);

        // Also add line orientation
        layer.setText('>     ', {repeat: true,
                                 offset: DETAIL_STYLE.weight,
                                 attributes: {'fill': DETAIL_STYLE.arrowColor,
                                              'font-size': DETAIL_STYLE.arrowSize}});
    });
});