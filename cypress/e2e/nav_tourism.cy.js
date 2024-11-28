describe('Create tourism event', () => {
    beforeEach(() => {
        const username = 'admin';
        const password = 'admin';

        cy.loginByCSRF(username, password);
        cy.mockTiles();
        cy.visit('/touristicevent/add/');
    });

    it('Should dynamically show/hide cancellation reason', () => {
       cy.wait('@tiles');
        // check initially hidden
        cy.get('#div_id_cancellation_reason').should("not.be.visible");
        // check toggle hide/show
        cy.get('#id_cancelled').check({force: true});
        cy.get('#div_id_cancellation_reason').should("be.visible");
        cy.get('#id_cancelled').uncheck({force: true});
        cy.get('#div_id_cancellation_reason').should("not.be.visible");
    });

    it('Should dynamically show/hide reservation text box', () => {
        // check initially hidden
        cy.get('#booking_widget').should("not.be.visible");
        // check toggle hide/show
        cy.get('#id_bookable').check({force: true});
        cy.get('#booking_widget').should("be.visible");
        cy.get('#id_bookable').uncheck({force: true});
        cy.get('#booking_widget').should("not.be.visible");
    });
});
