const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://geotrek.local:8000',
  },
  video: false,
  defaultCommandTimeout: 1800000, // 30min
  requestTimeout: 1800000,
  responseTimeout: 1800000,
  projectId: "ktpy7v"
});