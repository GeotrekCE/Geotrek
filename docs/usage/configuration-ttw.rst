=============
Paramétrage
=============


Accès interface admin
=====================

Menu à droite > admin

.. figure:: /images/admin/capture-admin.png
   :alt: Capture lien admin

   Capture lien admin

Paramétrages des modules
========================

Itinéraires
-----------

-  Pratiques
-  Accessibilités
-  Niveaux de difficulté
-  Thèmes
-  Types de services
-  Types de POIs

|image4|

Exemple : ajouter une pratique
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Dans admin, à la ligne “Pratiques” cliquer sur “+ ajouter”
-  Remplir les champs (en gras les champs obligatoires)

(note : la couleur n’est utilisée que pour le mobile actuellement)

|image5|


.. _sites-et-parcours-outdoor-1:

Sites et parcours outdoor
-------------------------

-  Cotations
-  Filières
-  Pratiques
-  Types de parcours
-  Types de site
-  Échelles de cotation


Plongées
--------

-  Niveau de difficulté
-  Niveau technique
-  Pratique


Tourisme
--------

-  Autres sports : catégorie activités → Types de contenus touristiques
-  Lieux de renseignements
-  Types de lieux de renseignement
-  Types d’événement touristiques
-  Systèmes de réservation

|image6|


Exemple : catégorie de contenu touristique et ses sous-type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

|image7|


Pour chaque catégorie il est possible de définir deux listes de
sous-type et leur nom.

Édition des sous-types de la catégorie “Hébergements”

.. figure:: /images/admin/django-admin-categorie-contenu-touristique-sous-types.png
   :alt: Sous-types de la catégorie “Hébergements”

   Sous-types de la catégorie “Hébergements”


Dans l’édition d’un contenu touristique de catégorie “Hébergement”

|image8|


Zones
-----

-  Communes
-  Secteurs
-  Zones sensibles et types de zones


Gestion des utilisateurs
========================

Dans Geotrek, il est possible de créer et de paramétrer des profils d'utilisateurs, possédants chacun des droits spécifiques et rattachés à des structures. La gestion des utilisateurs et des groupes est basé sur le `système d'authentification de Django <https://docs.djangoproject.com/fr/4.0/topics/auth/>`_.
Pour cela les objets suivants dans l'interface d'administration doivent être utilisés :

|image9|

Utilisateurs et droits
----------------------

Une fois un utilisateur créé avec les informations minimales, il est possible de lui octroyer un certain nombre de permissions :

-  **Actif** : permet de déterminer si l'utilisateur peut se connecter à Geotrek-Admin ou non. 

  Il est préférable de désactiver un compte lorsqu'un utilisateur n'intervient plus sur Geotrek, plutôt que de le supprimer.
  En effet supprimer le compte supprimera également par exemple toutes les entrées dans l'historique de Geotrek associées à ce compte.

-  **Statut équipe** : si la case est cochée l'utilisateur pourra accéder à l'interface d'administration de Geotrek-Admin

-  **Statut super-utilisateur** : permet d'octroyer toutes les permissions à un utilisateur sans avoir à les définir explicitement

Il est possible pour un utilisateur, de lui donner des permissions spécifiques. Celles-ci sont déterminées par type d'objet. 
  Pour cela il faut sélectionner les permissions dans l'écran de gauche pour les positionner dans l'écran de droite.
  Par exemple sur la capture ci-dessous l'utilisateur possède les permissions pour consulter uniquement et exporter les informations relatives aux 
  signalétiques sans possibilité d'accéder aux autres modules ou de modifier les contenus.

|image10|

Cette gestion fine des droits permet de déterminer les différents accès aux modules pour chaque utilisateur. On retrouve généralement pour chaque type d'objet les permissions suivantes qu'il est possible de donner ou non à un utilisateur :
-  Lecture
-  Ecriture
-  Modification
-  Modification de la géométrie de l'objet
-  Publication
-  Export

Groupes
-------

Pour faciliter l'opération de création d'utilisateurs et d'affectation de permissions, il existe un système de groupes dans Geotrek.
Pour chaque groupe il est possible d'associer un certain nombre de permissions.

Ensuite, dans la vue de modification de cet utilisateur, il suffira d'associer un utilisateur à un groupe pour bénéficier des permissions correspondantes.

Certains groupes existent par défaut dans Geotrek (Geotrek-rando, Lecteurs, Outdoor, Rédacteurs, Référents communication, Référents ronçons, Référents sentiers), mais il est bien entendu possible d'en ajouter d'autres pour refléter l'organisation de votre territoire.


Structures
----------

Chaque utilisateur est obligatoirement rattaché à une structure. Lors de l'installation, Geotrek crée une structure à laquelle les premiers utilisateurs seront rattachés.
Il est possible d'ajouter de nouvelles structures, reflétant des partenaires territoriaux, entreprises, entités qui seront ammenés à travailler à vos côté sur Geotrek.

Les utilisateurs d'une structure ne peuvent travailler que sur les objets dans Geotrek liés à leur structure. Ils pourront consulter les objets des autres structures mais n'auront pas le droit de les modifier.

Exemple : Si on imagine un Geotrek déployé sur l'ensemble du territoire français, il serait alors envisageable d'avoir des structures correspondantes aux régions. Chaque utilisateur sera rattaché à sa région correspondante. 
 Il y aura alors la garantie qu'un utilisateur de Bretagne ne puisse pas modifier les objets saisis par un utilisateur de Normandie.

Cette notion de structures permet de segmenter les périmètres d'action des utilisateurs et de permettre à différentes entités de travailler sur un même Geotrek-Admin, tout en garantissant une cohérence des données.

Deux précisions :
- Un utilisateur d'une structure pourra tout de même tracer des itinéraires sur des tronçons tracés par une autre structure
- Pour qu'un utilisateur puisse modifier les objets d'une autre structure il y a deux possibilités : soit celui-ci est super-utilisateur, soit il devra posséder la permission "Can by structure" qui permet d'outrepasser la restriction des structures.


Configuration des portails
==========================

Geotrek permet de configurer un ou plusieurs portails. Ce terme est utilisé pour référencer un site grand public sur lequel seront visibles les objets publiés de Geotrek.

Ainsi, il est possible d'avoir plusieurs Geotrek-Rando branchés sur un seul Geotrek-Admin. Grâce à leur distinction sous forme de portail, il sera alors aisé de choisir sur quel Geotrek-Rando on souhaite faire apparaitre une information.

Avec le widget Geotrek (https://github.com/GeotrekCE/geotrek-rando-widget) il est également possible d'utiliser cette fonctionnalité pour ditinguer les contenus à afficher dans un widget ou dans un autre.

Pour configurer un ou pluseurs portails, il faut se rendre dans l'interface d'administration sur la section "Portails cibles".

|image11|

Il est possible de choisir de publier sur un ou plusieurs portails les objets suivants : itinéraires, contenus et évènements touristiques, pages statiques. Pour cela il suffit de sélectionner la valeur souhaitée dans le champ "portail" à l'édition de l'objet.


Pictogrammes
============

Les pictogrammes contribués dans Geotrek doivent être au format :

* SVG (de préférence, cela permet de conserver la qualité en cas de redimensionnement) ou PNG,
* SVG pour les thèmes (afin de permettre un changement de couleur pour les thèmes sélectionnés),

Il doivent :

* Avoir un viewport carré afin de ne pas être déformés sur le portail,
* Ne pas déborder du cercle inscrit pour les pratiques et les catégories de contenus touristiques, en prévoyant une
  marge si nécessaire.
* Avoir une dimension minimale de 56x56 pixels en ce qui concerne les PNG

Si vous utilisez Inkscape, vous devez définir une viewBox. Voir http://wiki.inkscape.org/wiki/index.php/Tricks_and_tips#Scaling_images_to_fit_in_webpages.2FHTML

Afin de s'intégrer au mieux dans le design standard, les couleurs suivantes sont recommandées :

* Blanc sur fond transparent pour les pratiques et les catégories de contenus touristiques,
* Gris sur fond transparent pour les thèmes,
* Blanc sur fond orange pour les types de POI.


.. |image4| image:: /images/admin/django-admin-params-itineraires.png
.. |image5| image:: /images/admin/django-admin-ajout-pratique.png
.. |image6| image:: /images/admin/django-admin-params-tourisme.png
.. |image7| image:: /images/admin/django-admin-categorie-contenu-touristique.png
.. |image8| image:: /images/admin/contenu-touristique-categorie-sous-type.png
.. |image9| image:: /images/admin/django-admin-params-users.png
.. |image10| image:: /images/admin/django-admin-user-right.png
.. |image11| image:: /images/admin/portals.png
