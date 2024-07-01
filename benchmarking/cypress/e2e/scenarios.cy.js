describe('Benchmark scenarios', function() {
    before(function() {
        const username = 'geotrek';
        const password = 'geotrek';
        cy.loginByCSRF(username, password)
            .then((resp) => {
                expect(resp.status).to.eq(200);
            });
        cy.mockTiles();
    });

    it('Medium database, 100 via-points, backend cache', function() {
        cy.generateRouteTracingTimes('mediumDB3ViaPoints')
    })
})