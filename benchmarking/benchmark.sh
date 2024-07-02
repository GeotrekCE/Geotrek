#!/bin/bash

NB_MEASURES=15
MEASURES_DIR=./time_measures

launch_scenario() {
# $1 (string): cypress spec path
# $2 (boolean): if true, keep the backend cache before each spec run

    # Reset the time measure files
    if [ -d "$MEASURES_DIR" ]; then
        rm -f "$MEASURES_DIR"/time_measures_*
    else
        mkdir "$MEASURES_DIR"
    fi

    for i in $(seq 1 $NB_MEASURES)
    do
        if ! $2; then
            # Empty the backend cache
            curl 'http://geotrek.local:8000/admin/clearcache/' -X POST -H 'Cookie: csrftoken=jJPzy1w4p7KNspD9QG1Y2xOqG8Oczf2l; sessionid=xm0ia4g7gpjdtq9l85sbff3gscdlobfl' --data-raw 'csrfmiddlewaretoken=VihAxtR8JyN10VzyXyyEAUSiwWIbVnPG4RWZVkd2YvnEia2xD4psshwy2UmdksHR&cache_name=fat'
        fi
        # Launch the cypress test to take the time measures
        npx cypress run --spec $1 --browser edge
    done

    # Compute and display the average times
    echo "Scenario:" $1 >> "$MEASURES_DIR"/time_averages.txt
    echo "Backend cache:" $2 >> "$MEASURES_DIR"/time_averages.txt
    echo "Number of runs:" $NB_MEASURES >> "$MEASURES_DIR"/time_averages.txt
    python3 ./time_averages.py >> "$MEASURES_DIR"/time_averages.txt
    echo "" >> "$MEASURES_DIR"/time_averages.txt
}

# Reset the time averages files
if [ -d "$MEASURES_DIR" ]; then
        rm -f "$MEASURES_DIR"/time_averages.txt
    else
        mkdir "$MEASURES_DIR"
    fi
launch_scenario "cypress/e2e/mediumDB100ViaPts.cy.js" false
launch_scenario "cypress/e2e/mediumDB100ViaPts.cy.js" true
