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

Cypress.Commands.add('getCoordsOnMap', (pathPk, percentage) => {
  cy.getPath(pathPk).then(path => {
    let domPath = path.get(0);

    // Get the coordinates relative to the map element
    let pathLength = domPath.getTotalLength();
    let lengthAtPercentage = percentage * pathLength / 100;
    return domPath.getPointAtLength(lengthAtPercentage);
  })
});

Cypress.Commands.add('getCoordsOnPath', (pathPk, percentage) => {
  cy.getPath(pathPk).then(path => {
    cy.getCoordsOnMap(pathPk, percentage).then(coordsOnMap => {
      // Convert the coords so they are relative to the path
      cy.getMap().then(map => {
        let domMap = map.get(0);
        let domPath = path.get(0);

        // Get the coords of the map and the path relative to the root DOM element
        let mapCoords = domMap.getBoundingClientRect();
        let pathCoords = domPath.getBoundingClientRect();
        let horizontalDelta = pathCoords.x - mapCoords.x;
        let verticalDelta = pathCoords.y - mapCoords.y;

        // Return the coords relative to the path element
        return {
          x: coordsOnMap.x - horizontalDelta,
          y: coordsOnMap.y - verticalDelta,
        }
      });
    })

  })
})

Cypress.Commands.add('getMap', () => cy.get('[id="id_topology-map"]'));
Cypress.Commands.add('getPath', pathPk => cy.get(`[data-test=pathLayer-${pathPk}]`));

Cypress.Commands.add('clickOnPath', (pathPk, percentage) => {
  // Get the coordinates of the click and execute it
  cy.getCoordsOnPath(pathPk, percentage).then(clickCoords => {
    let startTime;
    cy.getPath(pathPk)
    .then((path) => {startTime = performance.now(); return path})
    .click(clickCoords.x, clickCoords.y, {force: true})
    // Return startTime so it is yielded by the command
    .then(() => startTime);
  });
});