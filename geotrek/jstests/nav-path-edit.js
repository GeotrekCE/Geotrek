var utils = require('./_nav-utils.js');

casper.test.begin('Edit an exist path', function(test) {

    casper.start(utils.baseurl + '/path/edit/1900/', function () {
        casper.waitForSelector('a.leaflet-draw-draw-polyline');
    });

    casper.then(function () {
        test.pass('Polyline control available.');
        test.assertElementCount('.leaflet-editing-icon', 5,
                                'Polyline handles are activated by default.');
    });

    casper.run(function done() {
        test.done();
    });
});
