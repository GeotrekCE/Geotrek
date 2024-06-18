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

        cy.get("textarea[id='id_topology']").type('[{"pk": 2, "kind": "TREK", "offset": 0.0, "paths": [3], "positions": {"0": [0.674882030756843, 0.110030805790642]}}]', {
            force: true,
            parseSpecialCharSequences: false
        })
        .then(() => {
            let elapsedTime = performance.now() - startTime
            cy.writeFile('benchmark_js.txt', elapsedTime.toString() + '\n', { flag: 'a+' })
        });
    })
})
