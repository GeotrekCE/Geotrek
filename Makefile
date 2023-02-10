build:
	docker build -t geotrek . --build-arg BASE_IMAGE_TAG=$(BASE_IMAGE_TAG)

build-no-cache:
	docker build -t geotrek --no-cache .

serve:
	docker-compose up

deps:
	docker-compose run --rm web bash -c "pip-compile -q && pip-compile -q requirements-dev.in"

flake8:
	docker-compose run --rm web flake8 geotrek

isort:
	docker-compose run --rm web isort geotrek

messages:
	docker-compose run --rm web ./manage.py makemessages -a --no-location

test:
	docker-compose run -e ENV=tests --rm web ./manage.py test

test_nds:
	docker-compose run -e ENV=tests_nds --rm web ./manage.py test

test_nav:
	casperjs test --baseurl=$(baseurl) geotrek/jstests/nav-*.js

test_export:
	casperjs test --baseurl=$(baseurl) geotrek/jstests/nav-auth.js geotrek/jstests/export-*.js

node_modules:
	npm install geotrek/jstests

test_js: node_modules
	./node_modules/.bin/mocha-phantomjs geotrek/jstests/index.html

tests: test test_js test_nav

update:
	docker-compose run web update.sh

load_data:
	docker-compose run web load_data.sh

load_demo:
	docker-compose run web ./manage.py loaddata development-pne

load_test_integration:
	docker-compose run web ./manage.py loaddata test-integration

css:
	for f in `find geotrek/ -name '*.scss'`; do node-sass --output-style=expanded $$f -o `dirname $$f`; done

%.pdf:
	mkdir -p docs/data-model
	postgresql_autodoc -h localhost -u geotrek -d geotrekdb -t dot -m "$*_.*" --password=geotrek -s "public"
	dot geotrekdb.dot -T pdf -o docs/data-model/$@
	rm geotrekdb.dot

authent.pdf:
	mkdir -p docs/data-model
	postgresql_autodoc -h localhost -u geotrek -d geotrekdb -t dot -m "auth(ent)?_.*" --password=geotrek -s "public"
	dot geotrekdb.dot -T pdf -o docs/data-model/authent.pdf
	rm geotrekdb.dot

global.pdf:
	postgresql_autodoc -h localhost -u geotrek -d geotrekdb -t dot --password=geotrek -s "public"
	dot geotrekdb.dot -T pdf -o docs/data-model/global.pdf
	rm geotrekdb.dot

uml: authent.pdf cirkwi.pdf core.pdf diving.pdf feedback.pdf flatpages.pdf infrastructure.pdf land.pdf maintenance.pdf outdoor.pdf sensitivity.pdf signage.pdf tourism.pdf trekking.pdf zoning.pdf global.pdf
