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

Cypress.Commands.add('getCoordsOnPath', (pathPk, percentage) => {
  cy.get(`[data-test=pathLayer-${pathPk}]`).then(path => {
    let domPath = path['0']
    
    // Get the coordinates relative to the map element
    let pathLength = domPath.getTotalLength()
    let lengthAtPercentage = percentage * pathLength / 100
    let coordsOnMap = domPath.getPointAtLength(lengthAtPercentage)

    // Convert the coords so they are relative to the path
    cy.get('[id="id_topology-map"]').then(map => {
      let domMap = map['0']

      // Get the coords of the map and the path relative to the root DOM element
      let mapCoords = domMap.getBoundingClientRect()
      let pathCoords = domPath.getBoundingClientRect()
      let horizontalDelta = pathCoords.x - mapCoords.x
      let verticalDelta = pathCoords.y - mapCoords.y

      // Return the coords relative to the path element
      return {
        x: coordsOnMap.x - horizontalDelta,
        y: coordsOnMap.y - verticalDelta,
      }
    })
  })
})

Cypress.Commands.add('clickOnPath', (pathPk, percentage, forceClick) => {
  // Get the click coordinates relative to the path
  cy.getCoordsOnPath(pathPk, percentage).then(clickCoords => {
    cy.get(`[data-test=pathLayer-${pathPk}]`)
    .click(clickCoords.x, clickCoords.y, {force: forceClick})
  })
})

// Cypress.Commands.add('addViaPoint', (srcPathPk, destPathPk) => {
//   cy.get(`[data-test=pathLayer-${srcPathPk}]`).as('srcPath')
//   cy.get(`[data-test=pathLayer-${destPathPk}]`).as('destPath')

//   cy.get('@srcPath').trigger('mousedown')
//   cy.get('@destPath').trigger('mouseup')

//   // cy.get('id="id_topology-map')
// })
