=======================
Pages statiques & menus
=======================

Les pages statiques sont les pages d'information et de contextualisation de votre portail web Geotrek-rando. Comme pourraient l'être les premières pages d'un topo-guide papier. Elles peuvent aussi être consultées dans votre application Geotrek-mobile.

.. figure:: ../images/user-manual/flatpages-gtecrins.jpg

    `Exemple de page statique <https://www.grand-tour-ecrins.fr/information/1-Le-Grand-Tour-des-Ecrins>`_

Les pages statiques permettent de fournir à l’internaute et futur randonneur des informations génériques : présentation de votre territoire, structures, partenaires, recommandations, informations pratiques, etc.

Elles sont gérées depuis le site d'administration de Geotrek-admin et sont ensuite publiées sur Geotrek-rando via l'API.

.. image:: ../images/user-manual/flatpages-adminsite.jpg

Du point de vue d'un portail de valorisation comme Geotrek-rando on parle des pages statiques par opposition aux pages « dynamiques » qui correspondent aux objets saisis dans les différents modules de Geotrek-admin (itinéraires, POIs, contenus et événements touristiques, sites et parcours Outdoor...). Ces derniers sont accessibles depuis la page de recherche avec ses filtres et la carte, ainsi qu'avec leurs pages de détails. Ces pages ne sont pas conçues manuellement mais sont un assemblage dynamique de multiples sources de données effectué par le logiciel Geotrek.

Pour rendre les pages statiques accessibles aux visiteurs, Geotrek-admin permet de gérer les menus dans le bandeau du portail Geotrek-rando. Les éléments du premier niveau sont toujours apparents (s'il y a assez d'espace d'affichage, ou dans un menu « Burger » sinon). Et il est possible de définir des éléments de menu dans un 2ème niveau, accessibles en déroulant les menus.

.. figure:: ../images/user-manual/flatpages_header_menus_example.png

    Exemple de menus déroulants définis dans Geotrek-admin

La section correspondante et le type d'entités s'appelle "Élément Menu", dans cette documentation on pourra parler de menu pour signifier les éléments de menu.

Les exemples de présentation visuelle des menus et des pages statiques décrivent la manière dont Geotrek-rando peut exploiter ces données et paramètrages. La présentation pourrait être différente si le portail n'est pas propulsé par Geotrek-rando.

Créer une page statique
========================

.. image:: ../images/user-manual/flatpages_admin_section_pages_statiques.png

Le formulaire de création/modification d'une page statique contient les champs suivants :

- **Titre \***
- Publiée
- Portails
- Sources
- Image de couverture
- Auteur image couverture
- Contenu
- Position
- Relative à

Seul le champ "Titre" est obligatoire pour créer une page statique.

Les champs "Titre", "Publiée" et "Contenu" peuvent recevoir une valeur différente pour chaque langue configurée.

*Titre*

    Il s'agit du titre de votre page qui sera visible et mis en avant sur la page elle-même. Le titre sert également à générer l'adresse web de la page.

*Publiée*

    Une page n'est visible sur le portail de valorisation que si elle a été publiée dans l'admin. On peut publier une page uniquement pour certaines langues.

*Portails*

    Ce champ ne concerne que les pages qui ne sont pas ciblées par un menu et les Geotrek-rando qui sont filtrés par portail. Permet de rendre la page visible sur certains portails pour y faire référence en-dehors des menus de navigation (dans le bas de page, dans le contenu d'une autre page, etc). Si une page est associée à un élément de menu, alors ce sera le (ou les) portail(s) associé(s) à cet élément de menu qui définira sur quel portail elle sera affichée et accessible.

*Sources*

    Permet d'attribuer une ou plusieurs sources au contenu de la page. Les sources peuvent être créées sur le site d'administration dans la section COMMUN ou directement avec le bouton + à côté de ce champ.

*Cover image*

    Permet de saisir une image grand format qui sera affichée en mode bandeau en haut de la page.

*Contenu*

    Le contenu de la page, sa mise en forme, les médias qui y sont insérés. Le contenu peut être traduit avec les valeurs spécifiques pour chaque langue configurée.

*Position* et *Relative à*

    Ces champs sont une alternative au glisser-déposer sur la liste des Pages Statiques et permettent de déplacer les pages dans l'arborescence (voir `Arborescence des pages statiques`_).

Mise en forme et médias
-----------------------

.. image:: ../images/user-manual/flatpages_tinymce_tools.png

Le champ "Contenu" expose un éditeur de texte riche (TinyMCE) permettant d'ajouter de la mise en forme et des médias dans le contenu de la page.

- mise en forme du texte : titres, style du texte, couleur du texte
- insertion de listes
- encart "Information"
- lien sous forme de bouton
- citation

Médias :

- insérer une image
- insérer une vidéo YouTube
- insérer un lien vers une autre page
- encart de suggestion de contenu Geotrek

Insérer une image
-----------------

.. image:: ../images/user-manual/flatpages_tinymce_tools_insert.png

L'outil *Insérer/modifier* une image permet d'insérer une image dans le contenu. Il est possible d'insérer une image déjà en ligne en renseignant son URL, ou de la télécharger sur le serveur. Privilégiez des images de taille suffisante, mais pas trop grande et volumineuse non plus car cela alourdira le chargement des pages inutilement. 

Les champs suivants sont à renseigner :

- Source
- Description alternative : non-affichée, pour l'accessibilité et les formes de consultation alternatives du contenu
- Largeur et Hauteur de présentation de l'image en pixels
- checkbox "Afficher le sous-titrage" insère une zone de texte collée à l'image pour afficher la légende et l'auteur de l'image (le titre est à saisir dans le contenu à la place du terme "Caption", une fois le formulaire d'ajout de l'image validé)

Une fois l'image chargée, il est possible de la redimensionner, et de l'aligner à gauche ou à droite du reste du contenu.

Insérer des suggestions de contenus Geotrek
-------------------------------------------

.. image:: ../images/user-manual/flatpages_tinymce_tools_geotrek.png

Avec l'outil *Suggestions*, les champs suivants sont à renseigner :

- le type de contenu (itinéraires, contenu touristique, événements ou site outdoor)
- les identifiants des contenus (séparés par des virgules. Par exemple : 12,8,73)
- un titre pour l'encart de suggestions

Après la validation du formulaire une zone récapitulant les informations saisies sous forme textuelle est placée dans le contenu de la page. Le portail Geotrek-rando enrichira la présentation des suggestions avec les titres des contenus suggérés à la place des identifiants et les images associées.

Vérifier la mise en page du contenu
-----------------------------------

.. image:: ../images/user-manual/flatpages_tinymce_tools_code.png

Les outils suivants sont disponibles :

- *Afficher les blocs* : permet de contrôler finement la séparation du contenu en blocs (pratique pour les paragraphes de texte)
- *Code source* : affiche et permet de modifier directement le contenu au format HTML (pour les utilisateurs avertis)

Il est aussi possible de prévisualiser une page statique avant de la rendre accessible à tous en l'associant à un élément de menu. Pour cela, créer la page, la publier et y accéder en saisissant son URL directement : ``https://URL-GEOTREK-RANDO/information/ID-PAGE`` (exemple : ``https://gtr3demo.ecrins-parcnational.fr/information/6``). Vous pourrez aussi alors récupérer son URL complète générée par Geotrek-rando, si vous souhaitez faire un lien vers cette page statique sans la rendre accessible depuis le menu.

Publier une page
================

Une page créée n'est pas immédiatement visible sur un portail Geotrek-rando. Il faut d'abord la marquer comme "Publiée" pour chacune des langues souhaitées. Il faut ensuite lui donner un moyen d'être accessible sur le site portail. Plusieurs options :

- faire figurer un lien vers la page dans les menus déroulants (voir `Arborescence de menus`_)
- placer la page dans l'arborescence des pages (voir `Arborescence des pages statiques`_)
- placer un lien direct dans une autre section du site : dans une page d'accueil personnalisée, dans un bas de page, etc.

Arborescence de menus
=====================

.. image:: ../images/user-manual/flatpages_admin_with_menuitems.png

La page listant les "Éléments Menus" indique la structure arborescente qui sous-tend les menus tels qu'ils apparaîtront sur le portail.

.. note::

    Un portail de type Geotrek-rando ne peut afficher que 2 niveaux de menus !

Chaque élément de menu a les champs suivants :

- *Titre*
- *Publié*
- *Portails*
- *Type de cible*
- [Si type de cible est "page"] la *page* cible
- [Si type de cible est "lien"] l'*URL du lien* (par langue) et checkbox *Ouvrir dans un nouvel onglet*
- *Position* et *Relative à*

Chaque élément de menu peut avoir une cible ou non. S'il a une cible le clic sur le menu y accédera. Il y a trois possibilités de cibles :

- une page statique Geotrek, avec le type de cible = "page"
- avec le type de cible = "lien" :
  + une page web externe sur un autre site web, par exemple ``https://fr.wikipedia.org/wiki/Randonnée``. Auquel cas une bonne pratique web est de l'ouvrir un nouvel onglet (checkbox cochée)
  + une page web interne au portail, typiquement une recherche pré-enregistrée, par exemple "/search?practices=4&difficulty=2&duration=1". Auquel cas une bonne pratique est de rester sur le même onglet (checkbox non-cochée)

Le champ *Plateforme* permet de différencier des menus destinés uniquement à un portail web ou uniquement à une application Geotrek-mobile. Cette possibilité de paramètrage sera bientôt supprimée.

Arborescence des pages statiques
================================

.. image:: ../images/user-manual/flatpages_admin_with_flatpages.png

Les pages statiques sont organisées dans une structure arborescente. Une page statique peut avoir des pages enfants et une unique page parente. L'arborescence des pages statiques permet d'organiser le contenu statique d'un portail d'une manière intelligible pour les visiteurs du site.

Les pages enfants sont accessibles depuis le bas d'une page parente dans Geotrek-rando.

Compatibilité de contenu créé avec l'ancien éditeur
===================================================

L'ancien éditeur de contenu des pages statiques (éditeur de grille avec Bootstrap) a été supprimé avec la déprécation de Geotrek-rando-v2.

Les pages statiques créées avec l'ancienne version de l'éditeur continueront de fonctionner sans changement sur le portail Geotrek-rando v3. Cependant il se peut que le balisage du contenu créé par l'ancien éditeur doive être retiré pour pouvoir utiliser à nouveau les styles et outils de mise en forme.

Comment procéder ?

- par précaution faire une copie du contenu, en incluant toutes les informations (URLs des images, etc)
- utiliser l'outil *code* ( ``< >`` ) pour obtenir une copie du contenu incluant les balises HTML
- retirer toutes les balises grâce à un outil en ligne (voir ci-dessous)
- remplacer l'ancien code avec le contenu nettoyé dans la fenêtre de l'outil *code*, valider
- refaire la mise en forme

.. seealso::

    Il existe beaucoup de service web pour nettoyer un contenu de ses balises HTML. Voici les deux premiers résultats provenant d'un moteur de recherche :

    - `Striphtml <https://striphtml.com/>`_
    - `W3docs <https://www.w3docs.com/tools/string-remove-tags>`_
