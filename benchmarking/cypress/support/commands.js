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

Cypress.Commands.add('getMap', () => cy.get('[id="id_topology-map"]'));
Cypress.Commands.add('getPath', pathPk => cy.get(`[data-test=pathLayer-${pathPk}]`));
Cypress.Commands.add('getRoute', stepIndex => {
  if (stepIndex == null)
    cy.get('[data-test^="route-step-"]')
  else
    cy.get(`[data-test="route-step-${stepIndex}"]`)
});

Cypress.Commands.add('fitPathsBounds', (pathPkList) => {
  cy.window().then(win => {
    const map = win.maps[0];
    const L = win.L;
    let bounds = L.latLngBounds([]);

    // For each path, extend the bounds so they include it
    cy.wrap(pathPkList).each(pk => {
      // Get the leaflet layer whose name contains the path pk
      const mapLayers = map._layers;
      const pathLayer = Object.values(mapLayers).find(layer => {
        return layer.properties?.name && layer.properties.name === "path "+ pk
      });
      bounds.extend(pathLayer.getBounds());
    }).then(() => {
      map.fitBounds(bounds)
    })
  })
})

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

Cypress.Commands.add('clickOnPath', (pathPk, percentage) => {

  // Zoom on the path for precision
  cy.window().then(win => {
    const map = win.maps[0];
    const originalMapBounds = map.getBounds();
    cy.fitPathsBounds([pathPk]).then(() => {

      // Get the coordinates of the click and execute it
      cy.getCoordsOnPath(pathPk, percentage).then(clickCoords => {
        cy.getPath(pathPk)
        .click(clickCoords.x, clickCoords.y, {force: true});
      })
      // Reset the map to its original bounds
      .then(() => map.fitBounds(originalMapBounds));
    })
  });
});


Cypress.Commands.add('addViaPoint', (src, dest, stepIndex) => {
  const {pathPk: srcPathPk, percentage: srcPathPercentage} = src
  const {pathPk: destPathPk, percentage: destPathPercentage} = dest

  cy.window().then(win => {
    const map = win.maps[0];
    const L = win.L;
    // Zoom on the paths for precision
    const originalMapBounds = map.getBounds();
    cy.fitPathsBounds([srcPathPk, destPathPk]).then(() => {

      // Get the coordinates of the mouse down and mouse up events
      cy.getCoordsOnMap(srcPathPk, srcPathPercentage).then(srcCoords => {
        cy.getCoordsOnMap(destPathPk, destPathPercentage).then(destCoords => {

          // Display the draggable marker by moving the mouse over a route layer
          map.fire('mousemove', {layerPoint: {x: srcCoords.x, y: srcCoords.y}})

          // Check that the draggable marker is displayed
          cy.get('.marker-drag').then(_ => {
            // Get the draggable marker layer corresponding to this step
            const mapLayers = map._layers;
            const draggableMarkers = Object.values(mapLayers).filter(layer => {
              return layer.classname === "marker-drag"
            })
            const draggableMarker = draggableMarkers[stepIndex]

            // Simulate dragging and dropping the marker onto the destination
            draggableMarker.fire('dragstart')
            const destLatLng = map.layerPointToLatLng(L.point(destCoords.x, destCoords.y))
            draggableMarker.setLatLng(destLatLng)
            draggableMarker.fire('dragend')
          });

        });
      })
      // Reset the map to its original bounds
      .then(() => map.fitBounds(originalMapBounds));
    });
  });
})
