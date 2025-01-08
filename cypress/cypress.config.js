const { defineConfig } = require("cypress");

module.exports = defineConfig({
  projectId: 'ktpy7v',
  redirectionLimit:400,
  requestTimeout: 50000,
  defaultCommandTimeout: 80000,
  screenshotsFolder: "screenshots",
  fixturesFolder: "fixtures",
  videosFolder: "videos",
  videos: true,
  e2e: {
    baseUrl: "http://geotrek.local:8000",
    supportFile: "support/e2e.js",
    specPattern: "e2e/**/*.cy.{js,jsx,ts,tsx}",
    },
  });
