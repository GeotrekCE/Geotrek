var casper = require('casper').create();

var baseurl = casper.cli.options['baseurl'];

casper.start(baseurl, function() {
    this.test.assert(this.getCurrentUrl().indexOf(baseurl + "/login/?next=/") == 0, 'url is the one expected');
});

casper.run(function() {
    this.test.renderResults(true, 0, this.cli.get('save') || false);
});
