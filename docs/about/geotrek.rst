=======
Geotrek
=======

.. _qu-est-ce-que-geotrek:

Qu'est ce que Geotrek ?
=======================

Geotrek est un ensemble d'outils web dédiés à la **gestion et la valorisation** des activités de randonnées, de sports de pleine nature et des informations touristiques.

Ils sont open source et peuvent ainsi être déployés librement par les structures et territoires qui le souhaitent, mais aussi les faire évoluer, ou bénéficier des évolutions réalisées par d'autres structures sans avoir à les re-financer.

Ces outils permettent la gestion de **nombreuses pratiques sportives** liées à des linéaires (randonnée pédestre, à vélo, en VTT, à cheval, avec poussette, etc.) mais également à des **contenus outdoor** non linéaires (escalade, vol libre, sports d’eau vive, etc.).

C’est l’**application de référence** des parcs naturels, mais aussi de nombreuses structures publiques (conseils départementaux, communautés de communes, comités régionaux du tourisme, offices du tourisme, etc.).

**Utiliser Geotrek vous permettra** :

* d’intégrer une **communauté de gestionnaires de randonnées très active**
* de **bénéficier de l’ensemble des évolutions** réalisées par les autres utilisateurs. Le projet est vivant et les outils s’améliorent sans cesse
* de disposer d’une **offre complète** qui pourra également être utilisée par d’autres acteurs du territoire
* de facilement pouvoir **accéder à d’autres fonctionnalités** quand le besoin s’en fera ressentir : site web, impression de fiches de parcours, gestion de la signalétique, organisation des travaux…
* d’exporter facilement vos contenus valorisables (itinéraires, POIs, contenus touristiques …) vers d’autres **plateformes touristiques nationales** (IGNrando', Visorando, Outdooractive, Apidae, Cirkwi, etc.)

Les quatre briques
==================

La suite logicielle Geotrek dispose de quatre briques à la fois distincts et complémentaires :

* :ref:`Geotrek-admin <qu-est-ce-que-geotrek>`: outil de gestion et de saisie de l’ensemble des informations, intégrant les données des Systèmes d’Informations Touristiques (SIT) et pouvant être connecté à votre SIG ou à des systèmes d’information transport
* `Geotrek-rando <https://geotrek-rando-v3.readthedocs.io/stable/>`_ : site web, reprenant les informations saisies dans Geotrek-admin, à destination des internautes grand public
* `Geotrek-mobile <https://github.com/GeotrekCE/Geotrek-mobile#geotrek-mobile>`_ : application mobile fonctionnant sous Android et iOS, reprenant des informations saisies dans Geotrek-admin et optimisées pour l’usage mobile (volume, impact sur la batterie, hors-ligne, géolocalisation…)
* `Geotrek-rando-widget <https://geotrek-rando-widget.readthedocs.io/>`_ : nouveau composant web permettant de valoriser une offre de contenus touristiques et de randonnées auprès des usagers du territoire, en l'intégrant dans un site internet existant

.. note::
  Cette documentation ne traite que de **Geotrek-Admin**, chaque brique ayant sa propre documentation.

Utilisateurs
============

L’application Geotrek, **destinée à deux types de public**, est une solution web qui apporte :

* des fonctionnalités de gestion des informations (itinéraires, sites outdoor, points d’intérêts, description, interprétation, médias…) et de gestion des infrastructures (signalétique, aménagements, travaux, réglementation…) pour les utilisateurs gérant un territoire (**Geotrek-admin**) 
* des fonctionnalités simples et ludiques de recherche et de consultation d’itinéraires pour les internautes et les mobinautes (**Geotrek-rando V3**, **Geotrek-mobile** et **Geotrek-rando-widget**).

Pour retrouver plus d'informations sur la suite applicative Geotrek, rendez-vous sur `geotrek.fr <https://geotrek.fr>`_.

A qui appartient Geotrek ?
==========================

Geotrek est un produit libre et open source avec une importante communauté d'utilisateurs.

Retrouvez toutes les infos sur la genèse du produit, son modèle communautaire ainsi que les principales structures contributrices sur le `site geotrek.fr <https://geotrek.fr/apropos.html>`_.

Comment rejoindre la communauté ?
==================================

* Rejoignez la `mailing list <https://groups.google.com/forum/#!forum/geotrek-fr>`_! Envoyez un mail à ``geotrek-fr+subscribe@googlegroups.com`` et vous recevrez automatiquement une invitation.
* `Ouvrir un ticket <https://github.com/GeotrekCE/Geotrek-admin/issues/new>`_ lorsqu'un bug est détecté
* `Ouvrir un ticket <https://github.com/GeotrekCE/Geotrek-admin/issues/new>`_ pour proposer une suggestion ou une nouvelle fonctionnalité
* Rejoindre le `canal de discussion Matrix <https://matrix.to/#/#geotrek:matrix.org>`_ afin d'échanger directement avec des membres de la communauté Geotrek

Composants libres
=================

L’application Geotrek utilise les technologies open source suivantes :

Geotrek-admin
-------------

* **Python / Django**, l'épine dorsale de l'application qui prend en charge les principales fonctionnalités comme le module de configuration, l'exploitation de la base de données, la gestion des utilisateurs et de leurs droits ou l'intégration avec les bibliothèques cartographiques. La richesse de son écosystème permet de concevoir des applications aux possibilités infinies, en favorisant la production d'applications sécurisées, solides (tests automatiques) et robustes (Python).
* **PostgreSQL / PostGIS** pour la base de données. La totalité des données de l'application est stockée dans une instance PostgreSQL avec l'extension spatiale PostGIS :

  * attributs, comptes utilisateurs…,
  * géométries,
  * raster (Modèle Numérique Terrain).

Geotrek-rando
-------------

* **Next.js** (*React, Typescript*), 
* **Leaflet**, utilisé comme librairie cartographique

Geotrek-rando-widget
---------------------

* **Stencil**, framework permettant de créer des composants web personnalisables et légers.
* **Leaflet**, utilisé comme librairie cartographique

Geotrek-mobile
---------------

* **Angular**, framework utilisé pour l'application Geotrek-mobile.
* **Ionic**, composant UI
* **Capacitor**, boîte à outils nécessaires à la création d'applications mobiles
* **MapLibre**, utilisé comme librairie cartographique 


