const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://geotrek.local:8000',
    // supportFile: "support.js",
    supportFile: false,
    specPattern: 'cypress/e2e/**/*.cy.js'
  },

  fixturesFolder: "fixtures",
  screenshotsFolder: "screenshots",
  videosFolder: "videos",
  video: true,
  requestTimeout: 50000,
  projectId: "ktpy7v"
  // integrationFolder: "scripts",
  // pluginsFile: false,
  // baseUrl: "http://geotrek.local:8000",
});
