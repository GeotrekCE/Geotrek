
#!/bin/bash

NB_MEASURES=5
MEASURES_DIR=./time_measures

# Reset the measure files
if [ -d "$MEASURES_DIR" ]; then
    rm -rf "$MEASURES_DIR"/*
else
    mkdir "$MEASURES_DIR"
fi

# Launch the cypress tests to take the time measures
for i in $(seq 1 $NB_MEASURES)
do
    npm run cypress:benchmark
done

# Compute the average times
python3 ./time_averages.py
