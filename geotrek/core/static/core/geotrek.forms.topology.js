L.FieldStore.TopologyStore = L.FieldStore.extend({

    lock: function () {
        this._locked = true;
    },

    unlock: function () {
        this._locked = false;
    },

    save: function (layer) {
        if (this._locked)
            return;
        L.FieldStore.prototype.save.call(this, layer);
    },

    _deserialize: function (value) {
        if (value === undefined || value === '')
            return null;
        if (typeof value == 'string')
            return JSON.parse(value);
        return value;
    },

    _serialize: function (layer) {
        var serialized;
        if (layer instanceof L.Marker) {
            var p = layer.getLatLng();
            serialized = {lat: p.lat, lng: p.lng};
            // In case the marker is snapped, serialize this information.
            if (layer.snap) {
                serialized['snap'] = layer.snap.properties.id;
            }
        }
        else {
            serialized = layer;  // Returned by TopologyHelper
        }
        return JSON.stringify(serialized);
    }
});


MapEntity.GeometryField.TopologyField = MapEntity.GeometryField.extend({
    options: {
        field_store_class: L.FieldStore.TopologyStore,
    },

    includes: MapEntity.GeometryField.GeometryFieldPathMixin,

    initialize: function () {
        MapEntity.GeometryField.prototype.initialize.apply(this, arguments);
        this.options.all_modifiable = this.options.modifiable;
        this.options.modifiable = false; // Will disable leaflet.draw in leaflet.forms.js
        this._objectsLayer = null;
        this._pathsLayer = null;
        this._pointControl = null;
        this._lineControl = null;
    },

    addTo: function (map) {
        MapEntity.GeometryField.prototype.addTo.call(this, map);
        this._initTopologyControl(map);
    },

    _initTopologyControl: function (map) {
        // This will make sure that we can't activate a control, while the
        // other is being used.
        var exclusive = new L.Control.ExclusiveActivation();

        if (this.options.is_point_topology) {
            addTopologyControl.call(this, '_pointControl', L.Control.PointTopology);
        }
        if (this.options.is_line_topology) {
            addTopologyControl.call(this, '_lineControl', L.Control.LineTopology);
        }

        function addTopologyControl(name, controlClass) {
            if (this.options.all_modifiable){
                var control = this[name] = new controlClass(map, this._pathsLayer, this);
                    map.addControl(control);
                    exclusive.add(control);
                    control.activable(false);
                control.handler.on('computed_topology', function (e) {
                    this.store.save(e.topology);
                }, this);
                // Make sure, we clean-up geometries when user changes from point to line
                control.handler.on('enabled', resetTopologies, this);
            }
            else {
                map.remove()
            };
        }

        function resetTopologies() {
            if (this._pointControl) this._pointControl.handler.reset();
            if (this._lineControl) this._lineControl.handler.reset();
        }
    },

    buildObjectsLayer: function () {
        this._objectsLayer = MapEntity.GeometryField.prototype.buildObjectsLayer.call(this);
        this._pathsLayer = this.buildPathsLayer(this._objectsLayer);
        this._pathsLayer.on('loaded', this._loadTopologyGraph, this);
        return this._objectsLayer;
    },

    _loadTopologyGraph: function () {
        // Make sure paths stay above other layers
        this._pathsLayer.bringToFront();

        // We now have the path, we can find out the topology bounds.
        var topo = this.store.load();
        if (topo)
            this._map.fitBounds(this._topologyBounds(topo));

        if (this._pointControl)
            this._pointControl.activable(true);
        if (this._lineControl)
            this._lineControl.activable(true);

        if (this._lineControl === null) {
            // No need to load graph for point topologies
            this.load();
            return;
        }

        // Path layer is ready, display the route
        this._pathsLayer.fire('data:loading');
        this.load();
        // For each path layer, set its data-test attribute
        this._pathsLayer.eachLayer((layer) => {
            layer._path.setAttribute('data-test', 'pathLayer-' + layer.properties.id)
        })
        this._pathsLayer.fire('data:loaded');
    },

    load: function () {
        if (this._pathsLayer === null) {
            // Use basic behaviour from MapEntityField until
            this._setView();
            return;
        }

        var topo = this.store.load();
        if (topo) {
            // Lock modification of initial value during load
            this.store.lock();
            console.debug("Deserialize topology: " + JSON.stringify(topo));
            if (this._lineControl && !topo.lat && !topo.lng) {
                this._lineControl.handler.restoreGeometry(topo)
            }
            if (this._pointControl && topo.lat && topo.lng) {
                this._pointControl.handler.restoreTopology(topo);
            }
            // Unlock now, user can edit
            this.store.unlock();
        }
    },

    _topologyBounds: function (topo) {
        var bounds = L.latLngBounds([]);
        if (topo.lat && topo.lng) {
            bounds.extend(L.latLng([topo.lat - 0.005, topo.lng - 0.005]));
            bounds.extend(L.latLng([topo.lat + 0.005, topo.lng + 0.005]));
        }
        else {
            var paths =  [];
            for (var i=0; i<topo.length; i++) {
                var subtopology = topo[i];
                for (var j=0; j<subtopology.paths.length; j++) {
                    var pathPk = subtopology.paths[j];
                    var pathLayer = this._pathsLayer.getLayer(pathPk);
                    bounds.extend(pathLayer.getBounds());
                }
            }
        }
        return bounds;
    }
});
