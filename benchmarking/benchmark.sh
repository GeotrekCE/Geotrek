#!/bin/bash

NB_MEASURES=5
MEASURES_DIR=./time_measures

launch_scenario() {
# $1 (string): cypress spec path
# $2 (boolean): if true, empty the backend cache before each spec run

    # Reset the measure files
    if [ -d "$MEASURES_DIR" ]; then
        rm -rf "$MEASURES_DIR"/*
    else
        mkdir "$MEASURES_DIR"
    fi

    for i in $(seq 1 $NB_MEASURES)
    do
        if $2; then
            # Empty the backend cache
            curl 'http://geotrek.local:8000/admin/clearcache/' -X POST -H 'Cookie: csrftoken=jJPzy1w4p7KNspD9QG1Y2xOqG8Oczf2l; sessionid=xm0ia4g7gpjdtq9l85sbff3gscdlobfl' --data-raw 'csrfmiddlewaretoken=VihAxtR8JyN10VzyXyyEAUSiwWIbVnPG4RWZVkd2YvnEia2xD4psshwy2UmdksHR&cache_name=fat'
        fi
        # Launch the cypress test to take the time measures
        npx cypress run --spec $1 --browser edge
    done

    # Compute and display the average times
    echo "Scenario:" $1
    echo "Backend cache:" $2
    python3 ./time_averages.py
}

launch_scenario "cypress/e2e/mediumDB100ViaPts.cy.js" true
launch_scenario "cypress/e2e/mediumDB100ViaPts.cy.js" false