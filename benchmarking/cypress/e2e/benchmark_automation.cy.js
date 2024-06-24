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
        }).as('graph')

        cy.visit('/trek/add');
        cy.wait('@tiles');

        // Write the request time after the response has been received
        cy.wait('@graph').then(intercept => {
            let elapsedTime = intercept.response.headers.elapsedTime
            cy.writeFile('benchmark_js.txt', elapsedTime.toString() + ' ', { flag: 'a+' })
        })

        // Click on the "Route" control
        let startTime;
        cy.get("a.linetopology-control").click()

        // Measure time for the next clicks
        for (let i = 0; i < 4; i++) {
            cy.get("a.linetopology-control").click().then(() => startTime = performance.now());
            cy.get('[id^="pathdef-"]')
            .then(() => {
                let elapsedTime = performance.now() - startTime
                cy.writeFile('benchmark_js.txt', elapsedTime.toString() + ' ', { flag: 'a+' })
            });
        }
        cy.writeFile('benchmark_js.txt', '\n', { flag: 'a+' })
    })
})
