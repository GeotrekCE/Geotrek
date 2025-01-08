============
Installation
============

.. contents::
   :local:
   :depth: 2


Ubuntu package
~~~~~~~~~~~~~~

Use these instructions to install Geotrek-admin in an easy way on a dedicated Ubuntu Focal Fossa 20.04 LTS server for production.
For another distributions, please use :ref:`the Docker installation method <docker-section>`. It requires more technical skills.
Lastly, for a developer instance, please follow :ref:`the dedicated procedure <development-section>`.


Requirements
------------

Geotrek is mostly a CPU-bound application due to the complex queries including geometric operations (such as intersection)
which are executed on the database. This is especially true in the setup with a Geotrek Rando v3 portal requesting
dynamic geometric data through the Geotrek API.

In such a configuration the required system resources should be:

* 4 cores
* 8 Go RAM or more
* 50 Go disk space or more (20 Go + estimated size of attached files like photos, including elements imported from SIT)

If spreading the components on multiple hosts keep in mind the bottleneck will most likely be the CPU and RAM at the
database server level.

Software requirements are :

* Ubuntu Focal Fossa 20.04 LTS. Server flavor is recommended but any other flavors work too (desktop…)

An Internet connection with open HTTP and HTTPS destination ports is required.


Information to prepare before installation
------------------------------------------

These information will be asked during the installation process and are the basic configuration of Geotrek-admin:

* The **domain name** or **IP** to use to access to **Geotrek-admin** web application.
* Rando server name: the **domain name** to use to access to **Geotrek-rando** website (optional, if appropriate).
* PostgreSQL **host, port, user, password and DB name** if you use an external DB server.
* The **SRID** of the projection to use to store geometries. The projection must match your geographic area and coordinates must be in meters.
* The list of **languages** into which translation of contents will be made
* The name or acronym of your **organization**


Fresh installation
------------------

Run the following command in a shell prompt on your server:

::

   curl https://raw.githubusercontent.com/GeotrekCE/Geotrek-admin/master/tools/install.sh | bash

If you don't want to use a local database, you can run the following command instead.
This will prevent the script to install PostgreSQL server locally.
Don't forget to enable PostGIS extension in your remote database before installation.

::

   curl https://raw.githubusercontent.com/GeotrekCE/Geotrek-admin/blob/master/tools/install.sh | bash -s - --nodb

Then create the application administrator account and connect to the web interface.

::

   sudo geotrek createsuperuser

If you are not confident with the ``install.sh`` script, or if you are having troubles, you can do the same operations by hand:

1. Add ``deb https://packages.geotrek.fr/ubuntu bionic main`` to APT sources list.
2. Add https://packages.geotrek.fr/geotrek.gpg.key to apt keyring.
3. Run ``apt-get update``
4. If you want to use a local database, install the pgRouting package by running ``sudo apt install -y postgresql-pgrouting wget software-properties-common`` (before installing Geotrek-admin, not at the same time).
   If not, you must create database and enable PostGIS and pgRouting extensions before.
5. Install the Geotrek-admin package (``sudo apt install geotrek-admin``).

.. note ::

    Geotrek-admin is automatically installed in ``/opt/geotrek-admin/`` directory.

    The installation automatically creates an internal ``geotrek`` linux user, owner of this directory

    The Geotrek-admin Python application is located in ``/opt/geotrek-admin/lib/python3.6/site-packages/geotrek`` directory


Extra steps
-----------

We highly recommend installing an antivirus software to regularly scan uploaded files located under ``/opt/geotrek-admin/var/media/``.

Here is the installation process for `ClamAV <https://www.clamav.net/>`_ :

::

   apt install clamav

Prepare quarantine folder for suspicious files :

::

   mkdir /var/lib/clamav/quarantine/
   chmod 700 /var/lib/clamav/quarantine/


Configure ClamAV via cron, to scan the folder once a day, put suspicious files in quarantine, and raise email alerts, by creating file ``/etc/cron.daily/clamscan`` with the following content :

::

   #!/bin/sh

   nice -n 15 ionice -c 3 clamscan --recursive --allmatch --suppress-ok-results --no-summary --infected --scan-mail=no --log=/var/log/clamav/scan-report.$(date -Iseconds) /opt/geotrek-admin/var/media/ |mail -E -s "ClamAV report for $(hostname)" admin@example.com

   # Cleanup old files in quarantine (> 90 days)
   find /var/lib/clamav/quarantine/ -type f -mtime +90 -delete

   # Cleanup old scan reports (> 365 days)
   find /var/log/clamav/ -type f -name "scan-report.*" -mtime +365 -delete


Make sure to change alert recepient (``admin@example.com`` above) and make this cron file executable :

::

   chmod 700 /etc/cron.daily/clamscan

If a suspicious file is put in quarantine, you will need to manually delete the corresponding attachment from Geotrek-Admin (since the file for this attachment has moved to the quarantine folder, it will no longer be found).


Uninstallation
--------------

Run:

::

   apt-get remove geotrek-admin

Media files will be left in ``/opt/geotrek-admin/var`` directory. To remove them, run:

::

   apt-get purge geotrek-admin

To remove dependencies (convertit, screamshooter…), run:

::

   apt-get autoremove

.. note::

    PostgreSQL and its database will not be removed by these commands. If need be, remove them manually.



.. _docker-section:

Docker
~~~~~~

Docker is an alternative installation method, recommended for experts only.
It allows to install several instances of Geotrek-admin on the same serveur,
and to install it on other distributions than Ubuntu Linux 18.04.


1. Install Docker and Docker Compose, either from your distribution or from upstream packages
   (cf. https://docs.docker.com/install/)
2. Download the code from https://github.com/GeotrekCE/Geotrek-admin/releases
   or checkout it with git from https://github.com/GeotrekCE/Geotrek-admin/
3. Unzip the tarball
4. Copy docker/install folder where you want
5. Edit ``docker-compose.yml`` to feed your needs if necessary
6. Copy ``.env.dist`` to ``.env`` and edit to feed your needs if necessary. Leave the ``GUNICORN_CMD_ARGS`` variable only if you're not using any other scaling system.
7. Create user and database, enable PostGIS extension
8. Run ``docker compose run --rm web update.sh``
9. Run ``docker compose up``
10. Install NGINX (or equivalent) and add a configuration file (taking inspiration from `nginx.conf.in`)

Management commands
-------------------

Replace ``sudo geotrek …`` commands by ``cd <install directory>; docker compose run --rm web ./manage.py …``

Replace ``sudo dpkg-reconfigure geotrek-admin`` by ``cd <install directory>; docker compose run --rm web update.sh``

To load minimal data and create an application superuser, run:

::

   docker compose run --rm web load_data.sh
   docker compose run --rm web ./manage.py createsuperuser
