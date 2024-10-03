FROM ubuntu:focal as base

ENV PYTHONBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV ENV=prod
ENV SERVER_NAME="localhost"
# If POSTGRES_HOST is empty, entrypoint will set it to the IP of the docker host in the container
ENV POSTGRES_HOST=""
ENV POSTGRES_PORT="5432"
ENV POSTGRES_USER="geotrek"
ENV POSTGRES_DB="geotrekdb"
ENV REDIS_HOST="redis"
ENV CONVERSION_HOST="convertit"
ENV CAPTURE_HOST="screamshotter"
ENV CUSTOM_SETTINGS_FILE="/opt/geotrek-admin/var/conf/custom.py"
ENV TZ=UTC

WORKDIR /opt/geotrek-admin
RUN mkdir -p /opt/geotrek-admin/var/log /opt/geotrek-admin/var/cache
RUN adduser geotrek --disabled-password && chown geotrek:geotrek -R /opt

RUN apt-get update -qq && apt-get install -yqq software-properties-common &&  \
    add-apt-repository  ppa:ubuntugis/ppa &&  \
    apt-get install -y -qq \
        python3.8 \
        ca-certificates \
        gettext \
        postgresql-client \
        tzdata \
        netcat \
        gdal-bin \
        binutils \
        libproj-dev \
        unzip \
        less \
        iproute2 \
        nano \
        curl \
        software-properties-common \
        shared-mime-info \
        fonts-liberation \
        libssl-dev \
        libfreetype6-dev \
        libxml2-dev \
        libxslt-dev \
        libcairo2 \
        libpango1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf2.0-dev \
        libffi-dev \
        fonts-dejavu-core \
        libvips && \
    apt-get install -y --no-install-recommends postgis && \
    apt-get clean all && rm -rf /var/lib/apt/lists/* && rm -rf /var/cache/apt/*

USER geotrek
COPY --chown=geotrek:geotrek docker/scripts/* /usr/local/bin/
ENTRYPOINT ["/bin/sh", "-e", "/usr/local/bin/entrypoint.sh"]
EXPOSE 8000

FROM base as build

USER root

RUN apt-get update -qq && apt-get install -y -qq  \
    git \
    python3.8-dev \
    python3.8-venv \
    build-essential \
    libpq-dev &&\
    apt-get clean all && rm -rf /var/lib/apt/lists/* && rm -rf /var/cache/apt/*

USER geotrek
RUN python3.8 -m venv /opt/venv
RUN /opt/venv/bin/pip install --no-cache-dir -U pip setuptools wheel
COPY requirements.txt requirements.txt
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt -U

FROM build as dev

COPY dev-requirements.txt dev-requirements.txt
RUN /opt/venv/bin/pip install --no-cache-dir -r dev-requirements.txt
COPY ./docs/requirements.txt doc-requirements.txt
RUN /opt/venv/bin/pip install --no-cache-dir -r doc-requirements.txt

CMD ["./manage.py", "runserver", "0.0.0.0:8000"]

FROM base as prod

ENV ENV prod

COPY --chown=geotrek:geotrek --from=build /opt/venv /opt/venv
COPY --chown=geotrek:geotrek geotrek/ geotrek/
COPY --chown=geotrek:geotrek manage.py manage.py
COPY --chown=geotrek:geotrek VERSION VERSION
COPY --chown=geotrek:geotrek setup.cfg setup.cfg

RUN CUSTOM_SETTINGS_FILE= SECRET_KEY=tmp /opt/venv/bin/python ./manage.py compilemessages

USER root

RUN apt-get update -qq && apt-get -yqq full-upgrade && \
    apt-get clean all && rm -rf /var/lib/apt/lists/* && rm -rf /var/cache/apt/*

USER geotrek

CMD ["gunicorn", "geotrek.wsgi:application", "--bind=0.0.0.0:8000"]
