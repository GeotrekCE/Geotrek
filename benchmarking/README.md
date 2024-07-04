# Benchmarking of the route calculation systems
This benchmarking system allows to measure execution times (cache generation, requests, etc) to compare performances of several versions of the routing system.

## How it works
This benchmarking system uses a script that launches a Cypress spec file (a scenario) which plots a route using one version of the routing.

Time measurements are taken during the plotting, and this scenario is run a number of times, resulting in several values for each measure which will then be averaged.

This process of repeatedly running a scenario and getting the average measurements is executed twice: first emptying the backend cache before each run, and then keeping it. This way, one can obtain average execution times when plotting a route, with and without initial backend cache.

To compare several versions of the routing, this process has to be done with each version.

## How to use it
To compare two versions of the route calculation, follow these steps:
1. Switch to the first version of the routing system
2. If needed, add a custom topology and scenario (see below: 'How to create a new scenario') and ensure you are using the corresponding database
3. If needed, modify the measurements in the Python or Cypress code (see below: 'How to make custom measurements')
4. Launch the geotrek admin server
5. Go to the the `benchmarking/` directory
6. Launch the script using this command:
    ```
    ./benchmark.sh path_to_scenario session_id
    ```
    `path_to_scenario`: path to the Cypress spec file containing the scenario for which to take the measurements

    `session_id`: id of a valid session on the server (used by the script to clear the cache when needed)
7. When script execution is completed, you can find the output in `time_measure/time_averages.txt`:
    ```
    Branch: backend_routing_benchmark
    Scenario: cypress/e2e/mediumDB100ViaPts.cy.js
    Backend cache: false
    Number of runs: 15
    Python: [2357.8577518463135, 291.6573842366536, 272.33864466349286]
    JavaScript: [2418.733333333349, 481.58000000001243, 323.77999999996973, 372.513333333274, 1605.0466666667373]

    Branch: backend_routing_benchmark
    Scenario: cypress/e2e/mediumDB100ViaPts.cy.js
    Backend cache: true
    Number of runs: 15
    Python: [426.1796474456787, 419.2177454630534, 288.23556900024414]
    JavaScript: [496.8599999999627, 480.46666666660457, 358.0933333334513, 415.24666666686534, 431.48666666677843]
    ```
    `Branch`: the checked out branch when the script was run

    `Scenario`: path to the Cypress spec file containing the scenario that was run

    `Backend cache`: whether or not the backend cache was kept before running the scenario

    `Number of runs`: how many times the scenario was run before averaging the time measurements

    `Python`: average time measurements for Python code

    `JavaScript`: average time measurements for JavaScript code

8. **Save this output**, as the file will be overwritten next time the script is run
9. Switch to the second version of the routing system and repeat steps 3 to 8

## How to create a new scenario
Each scenario corresponds to a Cypress spec file you can find in `cypress/e2e/`. All the scenarios you can find there use the `generateRouteTracingTimes` custom command, which takes the name of a topology (defined as a fixture) and plots it, measuring the time between click and route display for each new marker.

#### If you simply want to use a custom topology
1. Duplicate one of the spec files mentionned above
2. Set the right `username` and `password` values for the login process in the `before` function
3. Add the topology you want to use in `fixtures/topologies.json` (only the positions and paths are needed)
4. Set the name of this topology as argument of the `generateRouteTracingTimes` command
5. You should also set a fitting description as first argument of the `it` function
6. Pass the path to this new spec file as argument when launching the script

#### If you want to use a completely different scenario
1. Create a new spec file in `cypress/e2e/`
2. Setup the login process in the `before` function in the same way as in the existing spec files
3. Create your custom scenario in a `it` function, as any other Cypress test
4. For taking measurements, see next section: 'How to make custom measurements'
5. Pass the path to this new spec file as argument when launching the script

## How to make custom measurements
During a scenario run, measurements are recorded in the `time_measures/` directory. This allows to access them later in order to compute average times.

#### Adding a Cypress measurement
Since browsers do not allow to write on an arbitrary location on the disk for security reasons, the JavaScript measurements file must be filled in from Cypress tests.

To append a measurement to the JavaScript time measures file which will later be used to compute average times, use:
```
cy.write('time_measures/time_measures_js.txt', measurement + ' ', {flag: 'a+'})
```
* Note the added space following the measurement: all time measures for a scenario run are written on the same line, allowing to then make the average of each column
* Make sure to use the `a+` flag so as not to overwrite the file

#### Adding a Python measurement
The file in which to write Python time measures is `time_measures/time_measures_py.txt`.
* As for Cypress, do not forget to add a space after each measurement
* Specify `newline=''` so all measurements for a scenario run are on the same line
* Make sure to open the file for appending so as not to overwrite the file

#### Removing an existing measurement
All measurements for the typical scenario (described above) can be found in custom Cypress commands in `cypress/support/commands.js`.

You can simply remove the `cy.write` call as well as any storing or computing of dates and times corresponding to this call.

## Additional adjustments
* The number of runs for each cycle (i.e. how many times a scenario is run before averaging the measurements) can be set in `benchmark.sh` by modify the value of `NB_MEASURES`
* The timeout for Cypress commands, requests, etc, and many other settings can be set in `cypress.config.js` ([click here to know more](https://docs.cypress.io/guides/references/configuration))
