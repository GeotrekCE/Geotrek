============
Contributing
============

.. contents::
   :local:
   :depth: 2

Conventions
-----------

* Before contributing, open an issue and discuss about it with community (is it a bug or a feature ? What is the best way to achieve my goal ?)
* Use flake8
* KISS & DRY as much as possible
* Elegant and generic is good, simple is better
* Separate bug fixes and new features in several pull requests.
* Open a new Pull Request in "Draft" status until tests passed. Use at least 'bug', 'improvement' or 'feature' label.
* Commits messages are explicit and mention issue number (``(ref #12)`` or ``(fixes #23)``), they should contains corresponding tag (see below)
* Features are developed in a branch and merged from Github pull-requests.

Definition of done
------------------

* ``docs/changelog.rst`` is up-to-date
* An explicit unit-test covers the bugfix or the new feature.
* A frontend test (:path:jstests/nav-\*.js) covers the navigation bug fix or feature
* A JS *Mocha* test (:path:jstests/tests.\*.js) covers the JavaScript bug fix or feature
* Unit-tests total coverage is above or at least equal with previous commits. Patch coverage is 100% on new lines.
* Settings have default value in ``settings/base.py``
* Installation instructions and documentation are up-to-date

Check TODO in the source tree:

::

   find geotrek | xargs egrep -n -i '(TODO|XXX|temporary|FIXME)'


Pull requests
-------------

Before creating a pull request, ensure you follow those rules :

* Follow the guidelines of this page
* Self-review your code
* Add comments in your code, particularly in hard-to-understand areas
* Make corresponding changes to the documentation
* There is tests that prove my fix is effective or that my feature works.
* All new lines of code are tested
* There is an entry in the changelog file (with the corresponding issue referenced)

It is important to add a label to the pull request corresponding to the perimeter. Release notes are generated according to labels of pull requests. This is the list of available labels for pull requests:

+-----------------+---------------+-----------------------+---------+
| Tag             | Branch prefix | Emoji code            | Unicode |
+=================+===============+=======================+=========+
| Improvements    | impr\_        | dizzy                 | 💫      |
+-----------------+---------------+-----------------------+---------+
| Bug fixes       | bug\_         | bug                   | 🐛      |
+-----------------+---------------+-----------------------+---------+
| Features        | feat\_        | sparkles              | ✨      |
+-----------------+---------------+-----------------------+---------+
| Documentation   | doc\_         | memo                  | 📝      |
+-----------------+---------------+-----------------------+---------+
| Maintenance     | maint\_       | building_construction | 🏗       |
+-----------------+---------------+-----------------------+---------+
| Refactor        | ref\_         | recycle               | ♻       |
+-----------------+---------------+-----------------------+---------+
| Dependencies    | dep\_         | arrow_up              | ⬆       |
+-----------------+---------------+-----------------------+---------+
| CI/CD           | cicd\_        | construction_worker   | 👷      |
+-----------------+---------------+-----------------------+---------+
| Performances    | perf\_        | zap                   | ⚡      |
+-----------------+---------------+-----------------------+---------+
| UI/UX           | uiux\_        | lipstick              | 💄      |
+-----------------+---------------+-----------------------+---------+
| Security        | sec\_         | lock                  | 🔒      |
+-----------------+---------------+-----------------------+---------+
| Translations    | trans\_       | globe_with_meridians  | 🌐      |
+-----------------+---------------+-----------------------+---------+
| Hotfix          | hot\_         | ambulance             | 🚑      |
+-----------------+---------------+-----------------------+---------+
| Breaking change | break\_       | boom                  | 💥      |
+-----------------+---------------+-----------------------+---------+

Commits in pull requests are following a naming convention in order to easily establish their perimeter. Commit is formated as ``emoji [tag] description of commit``.

You can use one of the above prefix for your commits but also one of the following (tags used only for commits, not for pull requests):

========= ========================= ========
Tag       Emoji code                Unicode
========= ========================= ========
Codestyle art                       🎨
Clean     fire                      🔥
Tests     white_check_mark          ✅
Release   bookmark                  🔖
Merge     twisted_rightwards_arrows 🔀
========= ========================= ========


Release
--------

On master branch:

* Update files *VERSION* and *docs/changelog.rst* to remove ``+dev`` suffix and increment version (please use semver rules)
* Run ``dch -r -D RELEASED``, update version in the same way and save
* Commit with message 'Release X.Y.Z' and push to ``master``
* Create new release with name 'Geotrek-admin X.Y.Z' on Github, with tag X.Y.Z, click on "Generate release notes"
* Wait for release to be published through CI
* Update files *VERSION* and *docs/changelog.rst* to add ``+dev`` suffix
* Run ``dch -v <version>+dev --no-force-save-on-release`` and save
* Commit with message 'Back to development' and push to ```master``

* When creating a new release 'X.Y.Z' on github, Github actions will generate the .deb package file, and publish it on https://packages.geotrek.fr (see ``.github/workflows/test.yml`` file for details)

Other ways to contribute
-------------------------

* Help the users and answers questions on the `mailing-list <https://groups.google.com/g/geotrek-fr>`_ ;
* `Open a ticket <https://github.com/GeotrekCE/Geotrek-admin/issues/new>`_ when you encounter a bug ;
* `Open a ticket <https://github.com/GeotrekCE/Geotrek-admin/issues/new>`_ when you have a suggestion or feature idea ;
* Translate the documentation ;
* Translate the menus, buttons and labels (we use `Weblate <https://weblate.makina-corpus.net>`_) ;
* Maintain the installation script for different Linux distributions (*requires some basic Linux skills*) ;
* Fix bugs or improve layout and apparence (*requires Webmaster skills*) ;
* Fix bugs or improve core modules (*requires python/Django skills*).

Join the `mailing list <https://groups.google.com/forum/#!forum/geotrek-fr>`_! Send an email to ``geotrek-fr+subscribe@googlegroups.com`` and you will receive an invitation automatically.