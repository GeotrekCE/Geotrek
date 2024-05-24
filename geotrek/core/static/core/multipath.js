L.Mixin.ActivableControl = {
    activable: function (activable) {
        /**
         * Allow to prevent user to activate the control.
         * (it is like setEnable(state), but ``enable`` word is used
         *  for handler already)
         */
        this._activable = activable;
        if (this._container) {
            if (activable)
                L.DomUtil.removeClass(this._container, 'control-disabled');
            else
                L.DomUtil.addClass(this._container, 'control-disabled');
        }

        this.handler.on('enabled', function (e) {
            L.DomUtil.addClass(this._container, 'enabled');
        }, this);
        this.handler.on('disabled', function (e) {
            L.DomUtil.removeClass(this._container, 'enabled');
        }, this);
    },

    setState: function (state) {
        if (state) {
            this.handler.enable.call(this.handler);
            this.handler.fire('enabled');
        }
        else {
            this.handler.disable.call(this.handler);
            this.handler.fire('disabled');
        }
    },

    toggle: function() {
        this._activable = !!this._activable;  // from undefined to false :)

        if (!this._activable)
            return;  // do nothing if not activable

        this.setState(!this.handler.enabled());
    },
};


L.Control.ExclusiveActivation = L.Class.extend({
    initialize: function () {
        this._controls = [];
    },

    add: function (control) {
        this._controls.push(control);
        var self = this;
        control.activable(true);
        control.handler.on('enabled', function (e) {
            // When this control is enabled, activate this one,
            // disable the others and prevent them to be activable.
            $.each(self._controls, function (i, c) {
                if (c != control) {
                    c.activable(false);
                }
            });
        }, this);

        control.handler.on('disabled', function (e) {
            // When this control is disabled, re-enable the others !
            // Careful, this will not take care of previous state :)
            $.each(self._controls, function (i, c) {
                c.activable(true);
            });
        }, this);
    },
});


L.Control.PointTopology = L.Control.extend({
    includes: L.Mixin.ActivableControl,

    statics: {
        TITLE: 'Point',
    },

    options: {
        position: 'topleft',
    },

    initialize: function (map, guidesLayer, field, options) {
        L.Control.prototype.initialize.call(this, options);
        this.handler = new L.Handler.PointTopology(map, guidesLayer, options);
        // Deactivate control once point is added
        this.handler.on('added', this.toggle, this);
    },

    onAdd: function (map) {
        this._container = L.DomUtil.create('div', 'leaflet-draw leaflet-control leaflet-bar leaflet-control-zoom');
        var link = L.DomUtil.create('a', 'leaflet-control-zoom-out pointtopology-control', this._container);
        link.href = '#';
        link.title = L.Control.PointTopology.TITLE;

        L.DomEvent.addListener(link, 'click', L.DomEvent.stopPropagation)
                  .addListener(link, 'click', L.DomEvent.preventDefault)
                  .addListener(link, 'click', this.toggle, this);
        return this._container;
    }
});


L.Handler.PointTopology = L.Draw.Marker.extend({
    initialize: function (map, guidesLayer, options) {
        L.Draw.Marker.prototype.initialize.call(this, map, options);
        this._topoMarker = null;
        this._guidesLayer = guidesLayer;

        map.on('draw:created', this._onDrawn, this);
    },

    reset: function() {
        if (this._topoMarker) {
            this._map.removeLayer(this._topoMarker);
        }
        this.fire('computed_topology', {topology: null});
    },

    restoreTopology: function (topo) {
        this._topoMarker = L.marker([topo.lat, topo.lng]);
        this._initMarker(this._topoMarker);
        if (topo.snap) {
            this._topoMarker.fire('move');  // snap to closest
        }
    },

    _onDrawn: function (e) {
        if (e.layerType === 'marker') {
            if (this._topoMarker !== null) {
                this._map.removeLayer(this._topoMarker);
            }

            this.fire('topo:created');
            this._topoMarker = L.marker(e.layer.getLatLng());
            this._initMarker(this._topoMarker);
        }
    },

    _initMarker: function (marker) {
        marker.addTo(this._map);
        L.DomUtil.addClass(marker._icon, 'marker-point');
        marker.editing = new L.Handler.MarkerSnap(this._map, marker);
        marker.editing.addGuideLayer(this._guidesLayer);
        marker.editing.enable();
        marker.on('move snap', function (e) {
            this.fire('computed_topology', {topology: marker});
        }, this);
        // Fire now : don't wait for move/snap (i.e. on click)
        this.fire('computed_topology', {topology: marker});
    },
});



L.Control.LineTopology = L.Control.extend({
    includes: L.Mixin.ActivableControl,

    statics: {
        TITLE: 'Route',
    },

    options: {
        position: 'topleft',
    },

    initialize: function (map, guidesLayer, field, options) {
        L.Control.prototype.initialize.call(this, options);
        this.handler = new L.Handler.MultiPath(map, guidesLayer, options);
    },

    onAdd: function (map) {
        this._container = L.DomUtil.create('div', 'leaflet-draw leaflet-control leaflet-bar leaflet-control-zoom');
        var link = L.DomUtil.create('a', 'leaflet-control-zoom-out linetopology-control', this._container);
        link.href = '#';
        link.title = L.Control.LineTopology.TITLE;

        L.DomEvent.addListener(link, 'click', L.DomEvent.stopPropagation)
                  .addListener(link, 'click', L.DomEvent.preventDefault)
                  .addListener(link, 'click', this.toggle, this);

        // Control is not activable until paths are loaded
        this.activable(false);

        return this._container;
    }
});


L.ActivableMarker = L.Marker.extend({
    initialize: function () {
        L.Marker.prototype.initialize.apply(this, arguments);
        this._activated = false;
        // Watch out if a callback is added and we are already in this state.
        // It won't be called !
        this.activate_cbs = [];
        this.deactivate_cbs = [];
    },

    activated: function() {
        return this._activated;
    },

    activate: function() {
        if (!this._activated) {
            for (var i = 0; i < this.activate_cbs.length; i++) {
                this.activate_cbs[i](this);
            }
            this._activated = true;
        }
    },

    deactivate: function() {
        if (this._activated) {
            for (var i = 0; i < this.deactivate_cbs.length; i++) {
                this.deactivate_cbs[i](this);
            }
            this._activated = false;
        }
    }
});


L.Handler.MultiPath = L.Handler.extend({
    includes: L.Mixin.Events,

    initialize: function (map, guidesLayer, options) {
        this.map = map;
        this._container = map._container;
        this._guidesLayer = guidesLayer;
        this._routeLayer = null
        this._currentStepsNb = 0
        this._previousStepsNb = 0
        this.options = options;
        this.spinner = new Spinner()

        // Is the currently displayed route valid? i.e are all its markers linkable?
        this._routeIsValid = null

        // markers
        this.markersFactory = this.getMarkers();

        // Init a fresh state
        this.reset();

        this.idToLayer = function(id) {
            return guidesLayer.getLayer(id);
        };

        this.stepIndexToLayer = function(idx, layerArray) {
            if (!layerArray)
                return null

            for (var i = 0; i < layerArray.length; i++) {
                var layer = layerArray[i]
                if (layer.step_idx == idx)
                    return layer
            }
            return null;
        };

        this.layersOrderedByIdx = function() {
            var layers = this._routeLayer ? this._routeLayer.__layerArray : []
            var sortedLayers = layers.toSorted((first, second) => {
                return first.step_idx - second.step_idx     
            })
            return sortedLayers
        }

        /*
         * Draggable via steps
         *
         * The following piece of code was also taken from formfield.js
         * It place is here, but needs refactoring to become elegant.
         */
        this.drawOnMouseMove = null;

        this.on('disabled', function() {
            this.drawOnMouseMove && this.map.off('mousemove', this.drawOnMouseMove);
        }, this);

        // Draggable marker initialisation and step creation
        var self = this;
        (function() {
            function dragstart(e) {
                var next_step_idx = self.draggable_marker.group_layer.step_idx + 1;
                self.addViaStep(self.draggable_marker, next_step_idx);
            }
            function dragend(e) {
                self.draggable_marker.off('dragstart', dragstart);
                self.draggable_marker.off('dragend', dragend);
                init();
            }
            function init() {
                self.draggable_marker = self.markersFactory.drag(new L.LatLng(0, 0), null, true);

                self.draggable_marker.on('dragstart', dragstart);
                self.draggable_marker.on('dragend', dragend);
                self.map.removeLayer(self.draggable_marker);
            }

            init();
        })();

        this.on('fetched_route', this.onFetchedRoute, this);
        this.on('invalid_route', this.onInvalidRoute, this);
    },

    setState: function(state, autocompute) {
        autocompute = autocompute === undefined ? true : autocompute;
        var self = this;

        // Ensure we got a fresh start
        this.disable();
        this.reset();
        this.enable();
        console.debug('setState('+JSON.stringify({start:{pk:state.start_layer.properties.id,
                                                         latlng:state.start_ll.toString()},
                                                  end:  {pk:state.end_layer.properties.id,
                                                         latlng:state.end_ll.toString()}})+')');

        this._onClick({latlng: state.start_ll, layer:state.start_layer});
        this._onClick({latlng: state.end_ll, layer:state.end_layer});

        state.via_markers && $.each(state.via_markers, function(idx, via_marker) {
            console.debug('Add via marker (' + JSON.stringify({pk: via_marker.layer.properties.id,
                                                               latlng: via_marker.marker.getLatLng().toString()}) + ')');
            self.addViaStep(via_marker.marker, idx + 1);
            self.forceMarkerToLayer(via_marker.marker, via_marker.layer);
        });
    },

    // Reset the whole state
    reset: function() {
        var self = this;

        this.showPathGeom(null);

        // remove all markers from PointOnPolyline objects
        this.steps && $.each(this.steps, function(i, pop) {
            self.map.removeLayer(pop.marker);
        });

        // reset state
        this.steps = [];

        this.marker_source = this.marker_dest = null;
    },

    // Activate/Deactivate existing steps and markers - mostly about (un)bindings listeners
    stepsToggleActivate: function(activate) {
        var cb;
        // /!\ Order in activation is important, first activate marker then pop
        // The marker.move listener must be set before the pop.move listener
        if (activate) {
            cb = function(pop) { pop.marker.activate(); pop.toggleActivate(true); }
        } else {
            cb = function(pop) { pop.marker.deactivate(); pop.toggleActivate(false); }
        }

        $(this.steps).each(function(i, pop) { pop && cb(pop); });
    },

    addHooks: function () {
        L.DomUtil.addClass(this._container, 'cursor-topo-start');
        this._guidesLayer.on('click', this._onClick, this);

        this.stepsToggleActivate(true);

        this.fire('enabled');
    },

    removeHooks: function() {
        L.DomUtil.removeClass(this._container, 'cursor-topo-start');
        L.DomUtil.removeClass(this._container, 'cursor-topo-end');
        this._guidesLayer.off('click', this._onClick, this);

        this.stepsToggleActivate(false);

        this.fire('disabled');
    },


    // On click on a layer with the graph
    _onClick: function(e) {
        if (this.steps.length >= 2) return;
        var self = this;

        var layer = e.layer
          , latlng = e.latlng
          , len = this.steps.length;

        var next_step_idx = this.steps.length;

        // 1. Click - you are adding a new marker
        var marker;
        if (next_step_idx == 0) {
            L.DomUtil.removeClass(this._container, 'cursor-topo-start');
            L.DomUtil.addClass(this._container, 'cursor-topo-end');
            marker = this.markersFactory.source(latlng);
            this.marker_source = marker;
        } else {
            L.DomUtil.removeClass(this._container, 'cursor-topo-start');
            L.DomUtil.removeClass(this._container, 'cursor-topo-end');
            marker = this.markersFactory.dest(latlng)
            this.marker_dest = marker;
        }

        var pop = self.createStep(marker, next_step_idx);

        pop.toggleActivate();

        // If this was clicked, the marker should be close enough, snap it.
        self.forceMarkerToLayer(marker, layer);

        pop.events.fire('placed');
    },

    forceMarkerToLayer: function(marker, layer) {
        var closest = L.GeometryUtil.closest(this.map, layer, marker.getLatLng());
        marker.editing._updateSnap(marker, layer, closest);
    },

    createStep: function(marker, idx) {
        var self = this;

        var pop = new Geotrek.PointOnPolyline(marker);
        this.steps.splice(idx, 0, pop);  // Insert pop at position idx

        pop.events.on('placed', () => {

            if (!pop.isValid()) { // If the pop was not dropped on a path
                if (pop.previousPosition) {
                    // If the pop was on a path before, set it to its previous position
                    pop.marker.setLatLng(pop.previousPosition.ll)
                    self.forceMarkerToLayer(pop.marker, pop.previousPosition.polyline);
                    if (!this._routeIsValid) {
                        // If the route is not valid, the marker must stay highlighted
                        L.DomUtil.removeClass(pop.marker._icon, 'marker-snapped');
                    }
                } else {
                    // If not, then it is a new pop: remove it
                    self.removeViaStep(pop)
                }
                return
            }

            pop.previousPosition = {ll: pop.ll, polyline: pop.polyline}

            var currentStepIdx = self.getStepIdx(pop)

            // Create the array of new step indexes after the route is updated
            var newStepsIndexes = []
            if (currentStepIdx > 0)
                newStepsIndexes.push(currentStepIdx - 1)
            newStepsIndexes.push(currentStepIdx)
            if (currentStepIdx < self.steps.length - 1)
                newStepsIndexes.push(currentStepIdx + 1)

            // Create the array of step indexes before the route is updated 
            var oldStepsIndexes
            if (this._currentStepsNb == this.steps.length)  // If a marker is being moved
                oldStepsIndexes = [...newStepsIndexes]
            else {  // If a marker is being added
                if (this._currentStepsNb == 1)  // If it's the destination
                    oldStepsIndexes = []
                else
                    oldStepsIndexes = newStepsIndexes.slice(0, -1)
            }

            this._previousStepsNb = this._currentStepsNb
            this._currentStepsNb = this.steps.length

            self.fetchRoute(oldStepsIndexes, newStepsIndexes, pop)
        });

        return pop;
    },

    // add an in between step
    addViaStep: function(marker, step_idx) {
        var self = this;

        // A via step idx must be inserted between first and last...
        if (! (step_idx >= 1 && step_idx <= this.steps.length - 1)) {
            throw "StepIndexError";
        }

        var pop = this.createStep(marker, step_idx);

        var removeOnClick = () => this.removeViaStepFromRoute(pop)

        pop.marker.activate_cbs.push(() => marker.on('click', removeOnClick));
        pop.marker.deactivate_cbs.push(() => marker.off('click', removeOnClick));

        // marker is already activated, enable removeOnClick manually
        marker.on('click', removeOnClick)
        pop.toggleActivate();
    },

    // Remove an existing step by clicking on it
    removeViaStepFromRoute: function(pop) {
        var step_idx = this.getStepIdx(pop)
        this.removeViaStep(pop, step_idx)
        this._previousStepsNb = this._currentStepsNb
        this._currentStepsNb = this.steps.length
        this.fetchRoute(
            [step_idx - 1, step_idx, step_idx + 1],
            [step_idx - 1, step_idx],
            pop
        );
    },

    // Remove a step from the steps list
    removeViaStep: function(pop, step_idx) {
        this.steps.splice(step_idx, 1)
        this.map.removeLayer(pop.marker)
    },

    getStepIdx: function(step) {
        return this.steps.indexOf(step);
    },

    getStepIdxFromMarker: function(marker) {
        for (var i = 0; i < this.steps.length; i++) {
            if (this.steps[i].marker === marker)
                return i;
        }
        return -1;
    },

    getCookie: function(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },

    fetchRoute: function(old_steps_indexes, new_steps_indexes, pop) {
        /*
            old_steps_indexes: indexes of the steps for which to update the route
            new_steps_indexes: indexes of these steps after the route is updated
            pop (PointOnPolyline): step that is being added/modified/deleted
        */

        var steps_to_route = []
        new_steps_indexes.forEach(idx => {
            steps_to_route.push(this.steps[idx])
        })

        function canFetchRoute() {
            if (steps_to_route.length < 2)
                return false;
            if (new_steps_indexes.length < 2)
                return false;
    
            for (var i = 0; i < steps_to_route.length; i++) {
                if (!steps_to_route[i].isValid())
                    return false;
            }
    
            return true;
        }

        if (canFetchRoute()) {
            this.spinner.spin(this._container);

            var sent_steps = []
            steps_to_route.forEach((step) => {
                var sent_step = {
                    lat: step.ll.lat,
                    lng: step.ll.lng,
                }
                sent_steps.push(sent_step)
            })
            
            fetch(window.SETTINGS.urls['route_geometry'], {
                method: 'POST',
                headers: {
                    "X-CSRFToken": this.getCookie('csrftoken'),
                    'Content-Type': 'application/json; charset=UTF-8',
                },
                body: JSON.stringify({
                    steps: sent_steps,
                })
            })
            .then(response => {
                if (response.status == 200)
                    return response.json()
                return Promise.reject(response)
            })
            .then(
                data => {  // Status code 200:
                    console.log('response data:', data)
                    if (data) {
                        var route = {
                            'geojson': data,
                            'old_steps_indexes': old_steps_indexes,
                            'new_steps_indexes': new_steps_indexes,
                        }
                        this.fire('fetched_route', route);
                    }
                },
                // If the promise was rejected:
                response => {
                    console.log("fetchRoute:", response)
                    this.fire('invalid_route', pop)
                }
            )
            .catch(e => console.log("fetchRoute", e))
            .finally(() => this.spinner.stop())
        }
    },

    restoreTopology: function (topo) {

        /*
         * Topo is a list of sub-topologies.
         *
         *  X--+--+---O-------+----O--+---+--X
         *
         * Each sub-topoogy is a way between markers. The first marker
         * of the first sub-topology is the beginning, the last of the last is the end.
         * All others are intermediary points (via markers)
         */
        var self = this;


        // Only first and last positions
        if (topo.length == 1 && topo[0].paths.length == 1) {
            // There is only one path, both positions values are relevant
            // and each one represents a marker
            var topo = topo[0]
              , paths = topo.paths
              , positions = topo.positions;

            var first_pos = positions[0][0];
            var last_pos = positions[0][1];

            var start_layer = this.idToLayer(paths[0]);
            var end_layer = this.idToLayer(paths[paths.length - 1]);

            var start_ll = L.GeometryUtil.interpolateOnLine(this.map, start_layer, first_pos).latLng;
            var end_ll = L.GeometryUtil.interpolateOnLine(this.map, end_layer, last_pos).latLng;

            var state = {
                start_ll: start_ll,
                end_ll: end_ll,
                start_layer: start_layer,
                end_layer: end_layer
            };
            this.setState(state);
        }
        else {
            var start_layer_ll = {}
              , end_layer_ll = {}
              , via_markers = [];

            var pos2latlng = function (pos, layer) {
                var used_pos = pos;
                if (pos instanceof Array) {
                    used_pos = pos[1];  // Default is second position (think of last path of topology)
                    if (pos[0] == 0.0 && pos[1] != 1.0)
                        used_pos = pos[1];
                    if (pos[0] == 1.0 && pos[1] != 0.0)
                        used_pos = pos[1];
                    if (pos[0] != 1.0 && pos[1] == 0.0)
                        used_pos = pos[0];
                    if (pos[0] != 0.0 && pos[1] == 1.0)
                        used_pos = pos[0];
                    console.log("Chose " + used_pos + " for " + pos);
                }
                var interpolated = L.GeometryUtil.interpolateOnLine(self.map, layer, used_pos);
                if (!interpolated) {
                    throw ('Could not interpolate ' + used_pos + ' on layer ' + layer.properties.id);
                }
                return interpolated.latLng;
            };

            for (var i=0; i<topo.length; i++) {
                var subtopo = topo[i]
                  , firsttopo = i==0
                  , lasttopo = i==topo.length-1;

                var paths = subtopo.paths
                  , positions = subtopo.positions || {}
                  , lastpath = paths.length-1;

                // Safety check.
                if (!('0' in positions)) positions['0'] = [0.0, 1.0];
                if (!(lastpath in positions)) positions[lastpath] = [0.0, 1.0];

                var firstlayer = self.idToLayer(paths[0])
                  , lastlayer = self.idToLayer(paths[lastpath]);

                if (firsttopo) {
                    start_layer_ll.layer = firstlayer;
                    start_layer_ll.ll = pos2latlng(positions['0'][0], firstlayer);
                }
                if (lasttopo) {
                    end_layer_ll.layer = lastlayer;
                    end_layer_ll.ll = pos2latlng(positions[lastpath][1], lastlayer);
                }
                else {
                    var layer = lastlayer
                      , ll = pos2latlng(positions[lastpath], layer);
                    // Add a via marker
                    via_markers.push({
                        layer: layer,
                        marker: self.markersFactory.drag(ll, null, true)
                    });
                }
            }

            var state = {
                    start_ll: start_layer_ll.ll,
                    end_ll: end_layer_ll.ll,
                    start_layer: start_layer_ll.layer,
                    end_layer: end_layer_ll.layer,
                    via_markers: via_markers
                };

            // Restore state as if a user clicks.
            this.setState(state);
        }
    },

    showPathGeom: function (layer) {
        // This piece of code was moved from formfield.js, its place is here,
        // not around control instantiation. Of course this is not very elegant.
        var self = this;
        if (!this.markPath)
            this.markPath = (function() {
                var current_path_layer = null;
                return {
                    'updateGeom': function(new_path_layer) {
                        var prev_path_layer = current_path_layer;
                        current_path_layer = new_path_layer;
                        
                        if (prev_path_layer) {
                            self.map.removeLayer(prev_path_layer);
                        }

                        if (new_path_layer) {
                            self.map.addLayer(new_path_layer);
                            new_path_layer.setStyle({'color': 'yellow', 'weight': 5, 'opacity': 0.8});
                            new_path_layer.eachLayer(function (l) {
                                if (typeof l.setText == 'function') {
                                    l.setText('>  ', {repeat: true, attributes: {'fill': '#FF5E00'}});
                                }
                            });
                        }
                    }
                }
            })();

            this.markPath.updateGeom(layer);
    },

    getMarkers: function() {
        var self = this;

        var map = this.map,
            guidesLayer = this._guidesLayer;

        // snapObserver and map are required to setup snappable markers
        // returns marker with an on('snap' possibility ?
        var dragging = false;
        function setDragging() { dragging = true; };
        function unsetDragging() { dragging = false; };
        function isDragging() { return dragging; };
        function activate(marker) {
            marker.dragging.enable();
            marker.editing.enable();
            marker.on('dragstart', setDragging);
            marker.on('dragend', unsetDragging);
        }
        function deactivate(marker) {
            marker.dragging.disable();
            marker.editing.disable();
            marker.off('dragstart', setDragging);
            marker.off('dragend', unsetDragging);
        }

        var markersFactory = {
            isDragging: isDragging,
            makeSnappable: function(marker) {
                marker.editing = new L.Handler.MarkerSnap(map, marker);

                marker.editing.addGuideLayer(guidesLayer);
                marker.editing.enable();

                marker.activate_cbs.push(activate);
                marker.deactivate_cbs.push(deactivate);
                marker.activate();
            },
            _generic: function (latlng, layer, classname, snappable) {
                var marker = new L.ActivableMarker(latlng, {draggable: true});
                map.addLayer(marker);
                marker.classname = classname;
                L.DomUtil.addClass(marker._icon, classname);

                if (snappable)
                    this.makeSnappable(marker);

                marker.dragging.enable();
                return marker;
            },
            source: function(latlng, layer) {
                return this._generic(latlng, layer, 'marker-source', true);
            },
            dest: function(latlng, layer) {
                return this._generic(latlng, layer, 'marker-target', true);
            },
            drag: function(latlng, layer, snappable) {
                return this._generic(latlng, layer, 'marker-drag', snappable);
            }
        };

        return markersFactory;
    },

    buildRouteLayers: function(data) {
        geojson = data.geojson
        old_steps_indexes = data.old_steps_indexes
        new_steps_indexes = data.new_steps_indexes

        var newRouteLayer = L.featureGroup()
        var newIndexOfPreviousLayer = -1
        
        // The layers before the modified portion are added as-is
        var oldLayers = this.layersOrderedByIdx()

        for (var i = 0; i < oldLayers.length && i < new_steps_indexes[0]; i++) {
            newRouteLayer.addLayer(oldLayers[i])
            newIndexOfPreviousLayer = oldLayers[i].step_idx
        }

        // The new steps are added
        for (var i = 0; i < new_steps_indexes.length - 1; i++) {
            newLayer = L.geoJson(geojson.geometries[i])
            newLayer.step_idx = ++newIndexOfPreviousLayer
            newRouteLayer.addLayer(newLayer);
        }

        // The last element of old_steps_indexes is where we start reusing the
        // previous layers again
        var old_steps_last_index = old_steps_indexes.at(-1)
        if (this._routeIsValid == false && this._previousStepsNb > this._routeLayer.__layerArray.length + 1) {
            // If a new via marker is isolated and is now being removed or modified,
            // the invalid part of the path was not displayed. So at this point,
            // there is one more step, but there isn't one more layer.
            // Hence, all following layer indexes must be left-shifted by 1.
            old_steps_last_index--
        }
        var layer = this.stepIndexToLayer(old_steps_last_index, oldLayers)
        if (layer) {
            layer.step_idx = ++newIndexOfPreviousLayer
            newRouteLayer.addLayer(layer)
        }

        // Go through the remaining previous layers
        for (var i = old_steps_last_index + 1; i < oldLayers.length; i++) {
            newRouteLayer.addLayer(oldLayers[i])
            oldLayers[i].step_idx = ++newIndexOfPreviousLayer
        }

        this._routeLayer = newRouteLayer
        return {
            layer: newRouteLayer,
            serialized: null, // TODO: set serialized to something
        }
    },

    onFetchedRoute: function(data) {
        var self = this;

        // Reset all the markers to 'snapped' appearance
        this.steps.forEach(step => {
            L.DomUtil.removeClass(step.marker._icon, 'marker-highlighted');
            L.DomUtil.removeClass(step.marker._icon, 'marker-disabled');
            L.DomUtil.addClass(step.marker._icon, 'marker-snapped');
            step.marker.activate();
        })

        var topology = this.buildRouteLayers(data);
        this.showPathGeom(topology.layer);
        this._routeIsValid = true
        this.fire('computed_topology', {topology: topology.serialized});

        // ## ONCE ##
        if (this.drawOnMouseMove) {
            this.map.off('mousemove', this.drawOnMouseMove);
        }

        var dragTimer = new Date();
        this.drawOnMouseMove = function(a) {
            var date = new Date();
            if ((date - dragTimer) < 25) {
                return;
            }
            if (self.markersFactory.isDragging()) {
                return;
            }            

            dragTimer = date;

            for (var i = 0; i < self.steps.length; i++) {
                // Compare point rather than ll
                var marker_ll = self.steps[i].marker.getLatLng();
                var marker_p = self.map.latLngToLayerPoint(marker_ll);

                if (marker_p.distanceTo(a.layerPoint) < 10) {
                    self.map.removeLayer(self.draggable_marker);
                    return;
                }
            }

            var MIN_DIST = 30;

            var layerPoint = a.layerPoint
              , min_dist = Number.MAX_VALUE
              , closest_point = null
              , matching_group_layer = null;

            topology.layer && topology.layer.eachLayer(function(group_layer) {
                group_layer.eachLayer(function(layer) {
                    var p = layer.closestLayerPoint(layerPoint);
                    if (p && p.distance < min_dist && p.distance < MIN_DIST) {
                        min_dist = p.distance;
                        closest_point = p;
                        matching_group_layer = group_layer;
                    }
                });
            });

            if (closest_point) {
                self.draggable_marker.setLatLng(self.map.layerPointToLatLng(closest_point));
                self.draggable_marker.addTo(self.map);
                L.DomUtil.addClass(self.draggable_marker._icon, self.draggable_marker.classname);
                self.draggable_marker._removeShadow();
                self.draggable_marker.group_layer = matching_group_layer;
            } else {
                self.draggable_marker && self.map.removeLayer(self.draggable_marker);
            }
        };

        this.map.on('mousemove', this.drawOnMouseMove);
    },

    onInvalidRoute: function(pop) {
        this._routeIsValid = false

        if (this.steps.length <= 2)
            return

        // Highlight the invalid marker
        L.DomUtil.removeClass(pop.marker._icon, 'marker-snapped');
        L.DomUtil.addClass(pop.marker._icon, 'marker-highlighted');

        // Set the other markers to grey and disable them
        this.steps.forEach(step => {
            if (step._leaflet_id != pop._leaflet_id) {
                L.DomUtil.removeClass(step.marker._icon, 'marker-snapped');
                L.DomUtil.addClass(step.marker._icon, 'marker-disabled');
                step.marker.deactivate();
            }
        })
        // Prevent from creating new via-steps
        this.map.off('mousemove', this.drawOnMouseMove);
        this.map.removeLayer(this.draggable_marker);
    }

});

// pol: point on polyline
Geotrek.PointOnPolyline = function (marker) {
    this.marker = marker;

    // If valid:
    this.ll = null;
    this.polyline = null;

    // To reset the pop to its previous valid position when not dropped on a path:
    this.previousPosition = null;

    this.path_length = null;
    this.percent_distance = null;
    this._activated = false;

    this.events = L.Util.extend({}, L.Mixin.Events);

    this.markerEvents = {
        'move': function onMove (e) {
            var marker = e.target;
            if (marker.snap) marker.fire('snap', {layer: marker.snap, latlng: marker.getLatLng()});
        },
        'snap': function onSnap(e) {
            this.ll = e.latlng;
            this.polyline = e.layer;
            this.path_length = L.GeometryUtil.length(this.polyline);
            this.percent_distance = L.GeometryUtil.locateOnLine(this.polyline._map, this.polyline, this.ll);
            this.events.fire('valid');
        },
        'unsnap': function onUnsnap(e) {
            this.ll = null;
            this.polyline = null;
            this.events.fire('invalid');
        },
        'dragend': function onDragEnd(e) {
            this.events.fire('placed');
        }
    };
};

Geotrek.PointOnPolyline.prototype.activated = function() {
    return this._activated;
};

Geotrek.PointOnPolyline.prototype.toggleActivate = function(activate) {
    activate = activate === undefined ? true : activate;

    if ((activate && this._activated) || (!activate && !this._activated))
        return;

    this._activated = activate;

    var method = activate ? 'on' : 'off';

    var marker = this.marker
      , markerEvents = this.markerEvents;

    marker[method]('move', markerEvents.move, this);
    marker[method]('snap', markerEvents.snap, this);
    marker[method]('unsnap', markerEvents.unsnap, this);
    marker[method]('dragend', markerEvents.dragend, this);
};

Geotrek.PointOnPolyline.prototype.isValid = function(graph) {
    return (this.ll && this.polyline);
};
