describe('Nav tabs properties/attachments', () => {
    beforeEach(() => {
        const username = 'admin';
        const password = 'admin';

        cy.loginByCSRF(username, password);
        cy.mockTiles();
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
