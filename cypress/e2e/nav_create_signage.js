Cypress.on('uncaught:exception', (err, runnable) => {
    // returning false here prevents Cypress from
    // failing the test
    return false
})

describe('Create signage', () => {
    before(() => {
        const username = 'admin';
        const password = 'admin';

        cy.loginByCSRF(username, password)
            .then((resp) => {
                expect(resp.status).to.eq(200)
            });
        cy.mockTiles();
    })

    beforeEach(() => {
        cy.setCookie('django_language', 'en');
        Cypress.Cookies.preserveOnce('sessionid', 'csrftoken');
    });

    it('Create signage', () => {
        cy.visit('/signage/list');
        cy.wait('@tiles');
        cy.server()
        cy.route('/api/signage/drf/signages.geojson').as('signage')
        cy.get("a.btn-success[href='/signage/add/']").contains('Add a new signage').click()
        cy.wait('@signage')
        cy.get("a.pointtopology-control").click()
        cy.get('.leaflet-map-pane')
            .click(403, 287);
        cy.get("input[name='name_en']").type('Signage number 1')
        cy.get("a[href='#name_fr']").click()
        cy.get("input[name='name_fr']").type('Signalétique numéro 1')
        cy.get("select[id='id_type']").select("Service")
        cy.get('#save_changes').click()
        cy.url().should('not.include', '/signage/add/')
    })

    it('Liste signage', () => {
        cy.visit('/signage/list')
        cy.get("a[title='Signage number 1']").should('have.length', 1)
    })
})
