// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })

Cypress.Commands.add('loginByCSRF', (username, password) => {
    cy.request('/login/?next=/')
      .its('body')
      .then((body) => {
        // we can use Cypress.$ to parse the string body
        // thus enabling us to query into it easily
        const $html = Cypress.$(body)
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
      });
    });

Cypress.Commands.add('mockTiles', (username, password) => {
    cy.intercept("https://*.tile.opentopomap.org/*/*/*.png", {fixture: "images/tile.png"}).as("tiles");
});

Cypress.Commands.add('clickOnPath', (pathPk, percentage, forceClick) => {
  cy.get(`[data-test=pathLayer-${pathPk}]`).then(path => {
    let domPath = path['0']
    
    // Get the coordinates of the click relative to the map element
    let pathLength = domPath.getTotalLength()
    let lengthAtPercentage = percentage * pathLength / 100
    let coordsOnMap = domPath.getPointAtLength(lengthAtPercentage)

    // The click coords are relative to the map. Since we have to click on the
    // path, we convert the coords so they are relative to the path
    cy.get('[id="id_topology-map"]').then(map => {
      let domMap = map['0']

      // Get the coords of the map and the path relative to the root DOM element
      let mapCoords = domMap.getBoundingClientRect()
      let pathCoords = domPath.getBoundingClientRect()
      let horizontalDelta = pathCoords.x - mapCoords.x
      let verticalDelta = pathCoords.y - mapCoords.y

      // Get the coords of the click relative to the path element
      let coordsOnPath = {
        x: coordsOnMap.x - horizontalDelta,
        y: coordsOnMap.y - verticalDelta,
      }

      // Click on the path
      cy.wrap(path).click(coordsOnPath.x, coordsOnPath.y, {force: forceClick})
    })
  })
})
