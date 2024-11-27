describe('Login from home page / admin page', () => {

    beforeEach(() => {
        cy.setCookie('django_language', 'en');
    })

    it('Redirects to login page.', () => {
        cy.visit('/');
        cy.url().should('include', '/login/?next=/');
        cy.get('form');
        cy.contains("Username");
        cy.get('[name="username"]');
    })

    it('Fail to login', () => {
        cy.visit('/login/?next=/');
        cy.get('[name="username"]')
            .type('fake')
            .should('have.value', 'fake');
        cy.get('[name="password"]')
            .type('password')
            .should('have.value', 'password');
        cy.get("button[type='submit']").click();
        cy.url().should('include', '/login/?next=/');
    })

    it('Login', () => {
        cy.visit('/login/?next=/');
        cy.get('[name="username"]')
            .type('admin')
            .should('have.value', 'admin');
        cy.get('[name="password"]')
            .type('admin')
            .should('have.value', 'admin');
        cy.get("button[type='submit']").click();
        cy.url().should('include', '/path/list/');
        cy.url().should('not.include', '/login/?next=/');
    })

    it('Redirects to admin login page.', () => {
        cy.visit('/admin');
        cy.url().should('include', '/login/?next=/');
        cy.get('form');
        cy.contains("Username");
        cy.get('[name="username"]');
    })
})


describe('Logout', () => {
    beforeEach(() => {
        const username = 'admin';
        const password = 'admin';
        cy.loginByCSRF(username, password)
            .then((resp) => {
                expect(resp.status).to.eq(200)
            })
        Cypress.Cookies.preserveOnce('sessionid', 'csrftoken');
    })

    it('Logout', () => {
        cy.visit('/');
        cy.url().should('include', '/path/list/');
        cy.get("a.dropdown-toggle").contains('admin').click();
        cy.get("a[href='/logout/']").click();
        cy.url().should('include', '/login/');
    })
})
