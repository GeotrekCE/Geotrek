Cypress.Commands.add('loginByCSRF', (username, password) => {
  cy.session(
    [username, password],
    () => {
      cy.request('/login/')
      .its('body')
      .then((body) => {
        // we can use Cypress.$ to parse the string body
        // thus enabling us to query into it easily
        const $html = Cypress.$(body);
        cy.request({
          method: 'POST',
          url: '/login/?next=/',
          failOnStatusCode: true, // dont fail so we can make assertions
          form: true, // we are submitting a regular form body
          body: {
            username,
            password,
            "csrfmiddlewaretoken": $html.find('input[name=csrfmiddlewaretoken]').val(), // insert this as part of form body
         }
        });
        cy.setCookie('django_language', 'en');
      });
    },
    {
      validate() {
        cy.request('/').its('status').should('eq', 200);
      },
      cacheAcrossSpecs: true
    }
  );
});

Cypress.Commands.add('mockTiles', (username, password) => {
    cy.intercept("https://*.tile.opentopomap.org/*/*/*.png", {fixture: "images/tile.png"}).as("tiles");
});