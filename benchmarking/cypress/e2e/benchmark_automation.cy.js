Cypress.on('uncaught:exception', (err, runnable) => {
    // returning false here prevents Cypress from
    // failing the test
    return false
})

describe('Frontend-side routing', () => {
    before(() => {
        const username = 'admin';
        const password = 'admin';

        cy.loginByCSRF(username, password)
            .then((resp) => {
                expect(resp.status).to.eq(200);
            });
        cy.mockTiles();
    });

    it('Find a route', function () {
        // Set the response time in its header to access it later
        cy.intercept('/api/path/drf/paths/graph.json', request => {
            let startTime = performance.now()
            request.continue(response => {
                response.headers.elapsedTime = performance.now() - startTime
            })
        }).as('graph');

        cy.visit('/trek/add');
        cy.wait('@tiles');

        // Write the request time after the response has been received
        cy.wait('@graph').then(intercept => {
            let elapsedTime = intercept.response.headers.elapsedTime
            cy.writeFile('benchmark_js.txt', elapsedTime.toString() + ' ', { flag: 'a+' })
        });

        // Click on the "Route" control
        cy.get("a.linetopology-control").click();

        // Click on the paths and wait for the route to be displayed
        let startTime;
        cy.clickOnPath(3, 30);
        cy.clickOnPath(8, 90).then(() => startTime = performance.now());
        cy.getRoute().then(() => {
            let elapsedTime = performance.now() - startTime
            cy.writeFile('benchmark_js.txt', elapsedTime.toString() + '\n', { flag: 'a+' })
        });

        cy.addViaPoint({pathPk: 8, percentage: 10}, {pathPk: 7, percentage: 50}, 0)
        cy.addViaPoint({pathPk: 3, percentage: 20}, {pathPk: 4, percentage: 70}, 1)
    })
})
