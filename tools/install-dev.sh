#!/bin/bash

# This script is used to install Geotrek-admin >= 2.33, dev mode

set -e

if lsb_release -d | grep 'Ubuntu 20.04' > /dev/null; then
	echo "Ubuntu 20.04 found"
else
	echo "ERROR! Ubuntu 20.04 not found."
	exit 1
fi

if [ "`locale charmap`" != "UTF-8" ]; then
	echo "ERROR! Your user locale charmap is not UTF-8"
	exit 1
fi

if ! `localectl status | grep -q "System Locale: LANG=.*UTF-8"`; then
	echo "ERROR! Your system locale charmap is not UTF-8"
	exit 1
fi

if [ "$*" == "--nodb" ]; then
	postgis_and_routing=""
elif [ -n "$*" ]; then
	echo "Usage: $0 [--nodb]"
	exit 1
else
	postgis_and_routing="postgresql-pgrouting"
fi

sudo apt update
sudo apt install -y $postgis_and_routing wget software-properties-common
echo "deb [arch=amd64] https://packages.geotrek.fr/ubuntu $(lsb_release -sc) main dev" | sudo tee /etc/apt/sources.list.d/geotrek.list
wget -O- "https://packages.geotrek.fr/geotrek.gpg.key" | sudo apt-key add -
sudo apt update
sudo apt install -y geotrek-admin
