===============
Troubleshooting
===============

Geotrek-admin logs are stored in ``/opt/geotrek-admin/var/log/geotrek.log`` file.

But if Geotrek-admin does not start, take a look at systemd logs for each of the 3 Geotrek-admin services
(user web interface, API and asynchronous tasks):

::

   sudo journalctl -eu geotrek-ui
   sudo journalctl -eu geotrek-api
   sudo journalctl -eu geotrek-celery

The output is paginated. With -e option you are at the end of the logs but you can go up an down with arrows.
Type Q to quit. If you want to copy the log to a file, run:

::

   sudo journalctl -u geotrek-ui > systemd-geotrek-ui.log


Frequently encountered problems
-------------------------------

Error 500 with ``django.db.utils.IntegrityError … NOT NULL for column "language"``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``django.db.utils.IntegrityError: ERREUR:  une valeur NULL viole la contrainte NOT NULL de la colonne « language »``

This means specific migrations for translated fields have not been executed on database during update.
You have to run them manually, classical migrations included:

::

    geotrek migrate
    geotrek sync_translation_fields
    geotrek update_translation_fields
    geotrek update_geotrek_permissions
    geotrek update_post_migration_languages

Error 500 with document generation or map capture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Les captures de carte (utiles entre autre à la génération des documents et aux PDF) utilise un logiciel nommé screamshotter.
Ce logiciel, pilote un navigateur web (chromium, via puppeteer) qui va appeler la page web de geotrek-admin de l'objet dont il doit réaliser une capture de carte.

ex: ``https://mon-geotrek-admin.fr/trek/1/``

Il est donc nécessaire que cette URL lui soit accessible.

Paquet Debian :
  - l'URL utilisée depuis le navigateur (``https://mon-geotrek-admin.fr/trek/1/``) doit être accessible depuis l'hôte de l'application Geotrek-admin.

Image docker :
  - l'URL utilisée depuis le navigateur (``https://mon-geotrek-admin.fr/trek/1/``) doit être accessible depuis le container de l'application screamshotter (et convertit).

.. warning::
   Faites attention aux pare-feux, proxy et domaines privés. L'hôte (ou le container docker) doit pouvoir correctement résoudre l'adresse IP du domaine utilisé.

Sur certaines infrastructures, en particulier en entreprise ou derrière certains proxy, il se peut que la configuration de base empêche le bon fonctionnement.

**Exemple :**

- l'IP derriere le domaine demo-admin.geotrek.fr depuis mon poste de travail est 88.77.66.55, il s'affiche bien, mais depuis le serveur c'est 172.16.0.10, les captures de carte ne fonctionnent pas. Il faut jouer avec la configuration de la machine, les serveurs DNS, les paramètres network/alias ou extra_hosts du docker-compose.yml afin de le rendre accessible.
- le Proxy qui gère les certificats SSL ne transmet pas les bons en-têtes à geotrek-admin. De ce fait, geotrek-admin pense tourner en http et génère des url en http:// à screamshotter (ex: prend une capture de ``http://mon-geotrek-admin.fr/trek/1/`` au lieu de ``https://mon-geotrek-admin.fr/trek/1/``). Il faut penser à bien transmettre l'en-tête ``X-Forwarded-Proto https``.

Comment débloquer le bon fonctionnement ?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Tout d'abord, vérifiez que vous utilisez bien les dernières versions des outils screamshotter et convertit.


.. code-block:: bash

    sudo apt update
    sudo apt install screamshotter convertit


Pour docker

.. code-block:: bash

    docker compose pull screamshotter
    docker compose pull convertit

puis relancer toute l'application (down / up)


Vérifiez que l'URL de votre geotrek-admin est accessible depuis le serveur ou le container.

.. code-block:: bash

    wget https://mon-geotrek-admin.fr/trek/1/


Depuis docker :

.. code-block:: bash

    docker compose run --user root --rm screamshotter bash
    wget https://mon-geotrek-admin.fr/trek/1/


La réponse devrait ressembler à une page HTML de connexion.

Si ce n'est pas le cas, vérifiez l'IP du domaine

.. code-block:: bash

    ping mon-geotrek-admin.fr


La réponse doit être une IP publique, idéalement la même que depuis votre poste de travail.

Testez la capture de carte depuis geotrek-admin, sur une carte, le bouton avec un appareil photo.

Si ça ne fonctionne pas, vérifiez le message d'erreur :

Request on http://screamshotter:8000/?url=http%3A//mon-geotrek-admin.fr/trek/1/xxxx failed (status=500)

On peut voir que l'URL est **http** et non **https**, c'est un problème d'en-tête non transmis. Il faut régler ça au niveau du proxy.


Signature check for Debian packages
-----------------------------------

When you try to upgrade your Geotrek-admin, you can have problems with signature check:

::

   An error occurred while checking the signature.
   The repository is not updated and previous index files will be used.
   GPG error: https://packages.geotrek.fr/ubuntu bionic InRelease: The following signatures are invalid

You have to update the signature key to get the last update:

::

   wget -O- "https://packages.geotrek.fr/geotrek.gpg.key" | sudo apt-key add -


Show main packages versions
---------------------------

To debug or to report a bug, you can check or provide in issue the main versions of Geotrek-admin and its dependencies:

.. code-block:: bash

    geotrek check_versions


From docker:

.. code-block:: bash

    docker compose run --rm web ./manage.py check_versions


Some examples:

.. code-block:: bash

    geotrek check_versions --full
    geotrek check_versions --postgis


Check command help for more options:

.. code-block:: bash

    geotrek check_versions --help
