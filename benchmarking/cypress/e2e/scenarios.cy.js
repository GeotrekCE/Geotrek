import { routeTracing, CacheLevel } from "./benchmark_automation.cy";

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

    context('Medium database, 100 via-points, backend cache', function() {
        routeTracing('mediumDB100ViaPoints')
    })
})