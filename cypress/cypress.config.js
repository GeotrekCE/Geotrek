const { defineConfig } = require("cypress");

module.exports = defineConfig({
  projectId: 'ktpy7v',
  redirectionLimit:400,
  requestTimeout: 50000,
  defaultCommandTimeout: 80000,
  e2e: {
    baseUrl: "http://geotrek.local:8000",
    },
  },
});
