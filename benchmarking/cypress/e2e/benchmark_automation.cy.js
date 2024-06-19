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

    // TODO
    // beforeEach(() => {
    //     Cypress.Cookies.preserveOnce('sessionid', 'csrftoken');
    //     cy.setCookie('django_language', 'en');
    // });

    it('Find a route', () => {

        cy.visit('/trek/add');
        cy.wait('@tiles');

        // Get the graph and measure the response time
        let startTime;
        cy.then(() => startTime = performance.now());
        cy.intercept('/api/path/drf/paths/graph.json')
        .then(() => {
            let elapsedTime = performance.now() - startTime
            cy.writeFile('benchmark_js.txt', elapsedTime.toString() + ' ', { flag: 'a+' })
        });

        // Click on the "Route" control
        cy.get("a.linetopology-control").click();

        // Click on the paths and wait for the route to be displayed
        cy.get('[data-test="pathLayer-3"').click()
        cy.get('[data-test="pathLayer-8"').click({force: true})
        .then(() => startTime = performance.now())
        cy.get('[id^="pathdef-"')
        .then(() => {
            let elapsedTime = performance.now() - startTime
            cy.writeFile('benchmark_js.txt', elapsedTime.toString() + '\n', { flag: 'a+' })
        });
    })
})
