
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
    curl 'http://geotrek.local:8000/admin/clearcache/' -X POST -H 'Origin: http://geotrek.local:8000' -H 'Connection: keep-alive' -H 'Referer: http://geotrek.local:8000/admin/clearcache/' -H 'Cookie: csrftoken=jJPzy1w4p7KNspD9QG1Y2xOqG8Oczf2l; sessionid=xm0ia4g7gpjdtq9l85sbff3gscdlobfl; django_language=en' -H 'Upgrade-Insecure-Requests: 1' -H 'Priority: u=1' -H 'Pragma: no-cache' -H 'Cache-Control: no-cache' --data-raw 'csrfmiddlewaretoken=VihAxtR8JyN10VzyXyyEAUSiwWIbVnPG4RWZVkd2YvnEia2xD4psshwy2UmdksHR&cache_name=fat&clearcache=Clear+cache+now+%F0%9F%92%A3'
    npm run cypress:benchmark
done

# Compute the average times
python3 ./time_averages.py
