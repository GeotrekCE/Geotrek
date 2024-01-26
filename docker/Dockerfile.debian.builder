ARG DISTRO=ubuntu:focal

FROM ${DISTRO} as base


RUN apt-get update -qq -o Acquire::Languages=none && \
    env DEBIAN_FRONTEND=noninteractive apt-get install -yqq lsb-release && \
    if test "$(lsb_release -cs)" = 'focal' ; then \
       env DEBIAN_FRONTEND=noninteractive apt-get install -yqq software-properties-common wget && \
       printf "deb [arch=amd64] https://packages.geotrek.fr/ubuntu focal main" > /etc/apt/sources.list.d/geotrek.list && \
       wget -O- "https://packages.geotrek.fr/geotrek.gpg.key" | apt-key add - && \
       add-apt-repository ppa:jyrki-pulliainen/dh-virtualenv; fi &&\
    env DEBIAN_FRONTEND=noninteractive apt-get install -yqq \
    dpkg-dev \
    debhelper \
    dh-virtualenv \
    git \
    devscripts \
    equivs


WORKDIR /dpkg-build
COPY debian ./debian

RUN env DEBIAN_FRONTEND=noninteractive mk-build-deps --install --tool='apt-get -o Debug::pkgProblemResolver=yes --no-install-recommends --yes' debian/control

COPY . ./
WORKDIR /dpkg-build

RUN sed -i -re "1s/..UNRELEASED/.ubuntu$(lsb_release -rs)) $(lsb_release -cs)/" debian/changelog \
    && chmod a-x debian/geotrek.* \
    && dpkg-buildpackage -us -uc -b && mkdir -p /dpkg && cp -pl /geotrek[-_]* /dpkg \
    && dpkg-deb -I /dpkg/geotrek*.deb
WORKDIR /dpkg
