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

        // Get the graph and measure the execution time
        let startTime = 0
        cy.then(() => startTime = performance.now());
        cy.intercept('/api/path/drf/paths/graph.json')
        .then(() => {
            let elapsedTime = performance.now() - startTime
            cy.writeFile('benchmark_js.txt', elapsedTime.toString() + ' ', { flag: 'a+' })
            startTime = performance.now()
        });

        // Click on the "Route" control
        cy.get("a.linetopology-control").click();

        // Retrieve paths html elements
        cy.get('[data-test^="pathLayer-"').as('paths')
        cy.get('@paths').first().parent().next().children().first().click()
        cy.get('@paths').last().parent().prev().children().first().click({force: true})
        cy.get('[id^="pathdef-"').should('have.length', 3).then(() => {
            let elapsedTime = performance.now() - startTime
            cy.writeFile('benchmark_js.txt', elapsedTime.toString() + '\n', { flag: 'a+' })
        });
    })
})
