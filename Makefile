ifeq (, $(shell which docker-compose))
  docker_compose=docker compose
else
  docker_compose=docker-compose
endif

dep_update = uv pip compile -q --strip-extras pyproject.toml --output-file requirements.txt && uv pip compile pyproject.toml -c requirements.txt -q --strip-extras --extra dev --output-file dev-requirements.txt && uv pip compile --strip-extras -q docs/requirements.in --output-file docs/requirements.txt

-include Makefile.perso.mk

###########################
#          colors         #
###########################
PRINT_COLOR = printf
COLOR_SUCCESS = \033[1;32m
COLOR_DEBUG = \033[36m
COLOR_RESET = \033[0m

build:
	docker build -t geotrek . --build-arg BASE_IMAGE_TAG=$(BASE_IMAGE_TAG)

build-no-cache:
	docker build -t geotrek --no-cache .

build_deb:
	docker pull $(DISTRO)
	docker build -t geotrek_deb -f ./docker/Dockerfile.debian.builder --build-arg DISTRO=$(DISTRO) .
	docker run --name geotrek_deb_run -t geotrek_deb bash -c "exit"
	docker cp geotrek_deb_run:/dpkg ./
	docker stop geotrek_deb_run
	docker rm geotrek_deb_run

serve:
	$(docker_compose) up

deps:
	$(docker_compose) run --rm web bash -c "$(dep_update)"

ci_check_deps:
	$(dep_update)

flake8:
	$(docker_compose) run --rm web flake8 geotrek

messages:
	$(docker_compose) run --rm web ./manage.py makemessages -a --no-location --no-obsolete

compilemessages:
	$(docker_compose) run --rm web ./manage.py compilemessages

###########################
#        coverage         #
###########################
verbose_level ?= 1
report ?= report -m
.PHONY: coverage
coverage:
	rm ./var/.coverage* || true
	@$(PRINT_COLOR) "$(COLOR_SUCCESS) ### Start coverage ### $(COLOR_RESET)\n"
	$(docker_compose) run -e ENV=tests web coverage run --parallel-mode --concurrency=multiprocessing ./manage.py test $(test_name) --noinput --parallel -v $(verbose_level)
	$(docker_compose) run -e ENV=tests_nds web coverage run --parallel-mode --concurrency=multiprocessing ./manage.py test $(test_name) --noinput --parallel -v $(verbose_level)
	$(docker_compose) run -e ENV=tests web bash -c "coverage combine && coverage $(report)"
	rm ./var/.coverage*

test:
	$(docker_compose) run -e ENV=tests --rm web ./manage.py test --noinput --parallel

test_nds:
	$(docker_compose) run -e ENV=tests_nds --rm web ./manage.py test --noinput --parallel

test_nav:
	casperjs test --baseurl=$(baseurl) geotrek/jstests/nav-*.js

test_export:
	casperjs test --baseurl=$(baseurl) geotrek/jstests/nav-auth.js geotrek/jstests/export-*.js

node_modules:
	npm install geotrek/jstests

test_js: node_modules
	./node_modules/.bin/mocha-phantomjs geotrek/jstests/index.html

tests: test test_nds test_js test_nav

update:
	$(docker_compose) run web update.sh

load_data:
	$(docker_compose) run web load_data.sh

load_demo:
	$(docker_compose) run web ./manage.py loaddata development-pne

load_test_integration:
	$(docker_compose) run web ./manage.py loaddata test-integration

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
