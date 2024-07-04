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

    it('Big database, no via-point', function() {
        cy.generateRouteTracingTimes('bigDB25ViaPoints')
    })
})