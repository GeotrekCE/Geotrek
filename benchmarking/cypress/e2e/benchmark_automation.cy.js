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
            let startTime = Date.now()
            request.continue(response => {
                response.headers.elapsedTime = Date.now() - startTime
            })
        }).as('graph')

        cy.visit('/trek/add');
        cy.wait('@tiles');

        // Write the response time after it has been received
        cy.wait('@graph').then(intercept => {
            let elapsedTime = intercept.response.headers.elapsedTime
            cy.writeFile('benchmark_js.txt', elapsedTime.toString() + ' ', { flag: 'a+' })
        })

        // Click on the "Route" control
        cy.get("a.linetopology-control").click();

        // Click on the paths and wait for the route to be displayed
        let startTime;
        cy.get('[data-test=pathLayer-3]').click()
        cy.get('[data-test=pathLayer-8]').click({force: true})
        .then(() => startTime = performance.now())
        cy.get('[id^="pathdef-"]')
        .then(() => {
            let elapsedTime = performance.now() - startTime
            cy.writeFile('benchmark_js.txt', elapsedTime.toString() + '\n', { flag: 'a+' })
        });
    })
})
