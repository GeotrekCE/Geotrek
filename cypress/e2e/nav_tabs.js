describe('Nav tabs properties/attachments', () => {
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
        Cypress.Cookies.preserveOnce('sessionid', 'csrftoken');
        cy.setCookie('django_language', 'en');
    });

    it('Use tabs', () => {
        cy.visit('/trek/list');
        cy.get("a[title='Trek number 1']").should('have.attr', 'href')
            .then((href) => {
                cy.visit(href);
            });
        cy.get("a#tab-properties").should('have.class', 'active');
        cy.get("a#tab-attachments-accessibility").should('not.have.class', 'active');
        cy.get("a#tab-attachments-accessibility").click();
        cy.get("a#tab-attachments-accessibility").should('have.class', 'active');
        cy.get("a#tab-properties").should('not.have.class', 'active');
    });
});
