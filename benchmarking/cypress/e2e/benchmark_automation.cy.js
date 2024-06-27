Cypress.on('uncaught:exception', (err, runnable) => {
    // returning false here prevents Cypress from
    // failing the test
    return false
})

describe('Frontend-side routing', () => {
    before(() => {
        const username = 'geotrek';
        const password = 'geotrek';

        cy.loginByCSRF(username, password)
            .then((resp) => {
                expect(resp.status).to.eq(200);
            });
        cy.mockTiles();
    });

    it('100 via points', function () {
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
            cy.writeFile('time_measures/time_measures_js.txt', elapsedTime.toString() + ' ', { flag: 'a+' })
        });

        // Click on the "Route" control
        cy.get("a.linetopology-control").click();

        cy.fixture('topologies.json').then(topologies => {
            // Get the paths and positions for the start and end markers
            let topo = topologies.withViaPoints;
            const firstMarker = {
                path: topo[0].paths[0],
                position: topo[0].positions[0][0],
            };
            const lastMarker = {
                path: topo.at(-1).paths.at(-1),
                position: topo.at(-1).positions[Object.keys(topo.at(-1).positions).length - 1].at(-1),
            };

            // Add the start and end markers and wait for the route to be displayed
            let startTime;
            cy.clickOnPath(firstMarker.path, firstMarker.position * 100);
            cy.clickOnPath(lastMarker.path, lastMarker.position * 100)
            .then(() => startTime = performance.now());
            cy.getRoute().then(() => {
                let elapsedTime = performance.now() - startTime
                cy.writeFile('time_measures/time_measures_js.txt', elapsedTime.toString() + ' ', { flag: 'a+' })
            });

            // Add the via-points: for each step, drag from previous marker
            // and drop on last path and position of the current step
            let prevMarker = firstMarker;
            for (let step = 0; step < topo.length - 1; step++) {
                const viaMarker = {
                    path: topo[step].paths.at(-1),
                    position: topo[step].positions[Object.keys(topo[step].positions).length - 1].at(-1),
                };
                cy.addViaPoint(
                    {pathPk: prevMarker.path, percentage: prevMarker.position * 100},
                    {pathPk: viaMarker.path, percentage: viaMarker.position * 100},
                    step
                );
                prevMarker = viaMarker;
            }
        })

        // Add a newline to the time log files
        cy.writeFile('time_measures/time_measures_js.txt', '\n', { flag: 'a+' })
        cy.writeFile('time_measures/time_measures_py.txt', '\n', { flag: 'a+' })
    })
})
