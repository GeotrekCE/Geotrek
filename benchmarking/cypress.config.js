const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://geotrek.local:8000',
  },
  video: false,
  requestTimeout: 50000,
  projectId: "ktpy7v"
});
