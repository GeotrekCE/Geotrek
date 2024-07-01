const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://geotrek.local:8000',
  },
  video: false,
  defaultcommandTimeout: 5000000,
  requestTimeout: 5000000,
  responseTimeout: 5000000,
  projectId: "ktpy7v"
});