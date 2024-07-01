
#!/bin/bash

NB_MEASURES=5
MEASURES_DIR=./time_measures

# Reset the measure files
if [ -d "$MEASURES_DIR" ]; then
    rm -rf "$MEASURES_DIR"/*
else
    mkdir "$MEASURES_DIR"
fi

for i in $(seq 1 $NB_MEASURES)
do
    # Empty the backend cache
    curl 'http://geotrek.local:8000/admin/clearcache/' -X POST -H 'Cookie: csrftoken=jJPzy1w4p7KNspD9QG1Y2xOqG8Oczf2l; sessionid=xm0ia4g7gpjdtq9l85sbff3gscdlobfl' --data-raw 'csrfmiddlewaretoken=VihAxtR8JyN10VzyXyyEAUSiwWIbVnPG4RWZVkd2YvnEia2xD4psshwy2UmdksHR&cache_name=fat'
    # Launch the cypress test to take the time measures
    npx cypress run --spec cypress/e2e/mediumDB100ViaPts.cy.js --browser edge
done

# Compute the average times
python3 ./time_averages.py
