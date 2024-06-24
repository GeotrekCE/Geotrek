#!/bin/bash

NB_MEASURES=5
JS_MEASURES_FILE=./time_measures_js.txt
PY_MEASURES_FILE=./time_measures_py.txt

# Reset the measure files
rm $JS_MEASURES_FILE
rm $PY_MEASURES_FILE

# Launch the cypress tests to take the time measures
for i in $(seq 1 $NB_MEASURES)
do
    npm run cypress:benchmark
done

# Compute the average times
python3 ./time_averages.py