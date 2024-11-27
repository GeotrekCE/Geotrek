describe('Nav reports workflow', () => {
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

    it('Handles resolved intervention reports', () => {
        cy.visit('/report/12/')
        cy.wait('@tiles');
        cy.get(".btn.btn-primary.ml-auto").click()
        // Cannot use selectors for sentinel and supervisor messages yet
        cy.get("#id_message_sentinel_predefined").should("not.be.visible")
        cy.get("#id_message_sentinel").should("not.be.visible")
        cy.get("#id_message_administrators").should("not.be.visible")
        cy.get("#id_message_supervisor").should("not.be.visible")
        // Change selected status to resolved
        cy.get("#id_status").select("3")
        // Can use selectors for sentinel messages
        cy.get("#id_message_sentinel_predefined").should("be.visible")
        cy.get("#id_message_sentinel").should("be.visible")
        cy.get("#id_message_administrators").should("be.visible")
        cy.get("#id_message_supervisor").should("not.be.visible")
        // Select a predefined email
        cy.get("#id_message_sentinel_predefined").select("1")
        cy.get("#id_message_sentinel").should("have.value", "Pris en charge par Comm des Comm des Arbres Binaires le 17/05/2022")
        cy.get("#id_message_administrators").should("have.value", "Pris en charge par Comm des Comm des Arbres Binaires le 17/05/2022")
        // Remove predefined email
        cy.get("#id_message_sentinel_predefined").select("")
        cy.get("#id_message_sentinel").should("have.value", "")
        cy.get("#id_message_administrators").should("have.value", "")
        // Change selected status back to initial one
        cy.get("#id_status").select("1")
        // Cannot use selectors for sentinel and supervisor messages anymore
        cy.get("#id_message_sentinel_predefined").should("not.be.visible")
        cy.get("#id_message_sentinel").should("not.be.visible")
        cy.get("#id_message_administrators").should("not.be.visible")
        cy.get("#id_message_supervisor").should("not.be.visible")
    })


    it('Handles filed reports', () => {
        cy.visit('/report/13/')
        cy.get(".btn.btn-primary.ml-auto").click()
        // Cannot use selectors for sentinel and supervisor messages yet
        cy.get("#id_message_sentinel_predefined").should("not.be.visible")
        cy.get("#id_message_sentinel").should("not.be.visible")
        cy.get("#id_message_administrators").should("not.be.visible")
        cy.get("#id_message_supervisor").should("not.be.visible")
        // Change assigned user
        cy.get("#id_assigned_user").select("5")
        // Can use selectors for sentinel and supervisor messages
        cy.get("#id_message_sentinel_predefined").should("be.visible")
        cy.get("#id_message_sentinel").should("be.visible")
        cy.get("#id_message_administrators").should("be.visible")
        cy.get("#modelfields").scrollTo('bottom').get("#id_message_supervisor").should("be.visible")
        // Select a predefined email
        cy.get("#id_message_sentinel_predefined").select("2")
        cy.get("#id_message_sentinel").should("have.value", "Faire attention a la marche")
        cy.get("#id_message_administrators").should("have.value", "Faire attention a la marche")
        cy.get("#id_message_supervisor").should("have.value", "")
        // Select another predefined email
        cy.get("#id_message_sentinel_predefined").select("3")
        cy.get("#id_message_sentinel").should("have.value", "Ce probleme n'en sera bientot plus un")
        cy.get("#id_message_administrators").should("have.value", "Ce probleme n'en sera bientot plus un")
        // Remove predefined email
        cy.get("#id_message_sentinel_predefined").select("")
        cy.get("#id_message_sentinel").should("have.value", "")
        cy.get("#id_message_administrators").should("have.value", "")
        // Change assigned user back
        cy.get("#modelfields").scrollTo('bottom').get("#id_assigned_user").should("be.visible")
        cy.get("#id_assigned_user").select("9")
        // Cannot use selectors for sentinel and supervisor messages anymore
        cy.get("#id_message_sentinel_predefined").should("not.be.visible")
        cy.get("#id_message_sentinel").should("not.be.visible")
        cy.get("#id_message_administrators").should("not.be.visible")
        cy.get("#id_message_supervisor").should("not.be.visible")
    })

})
