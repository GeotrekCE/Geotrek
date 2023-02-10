============
Contributing
============

Conventions
-----------

* Before contributing, open an issue and discuss about it with community (is it a bug or a feature ? What is the best way to achieve my goal ?)
* Use flake8 and isort
* KISS & DRY as much as possible
* Elegant and generic is good, simple is better
* Separate bug fixes and new features in several pull requests.
* Open a new Pull Request in "Draft" status until tests passed. Use at least 'bug', 'improvement' or 'feature' label.
* Commits messages are explicit and mention issue number (``(ref #12)`` or ``(fixes #23)``)
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


Release
-------

On master branch:

* If need be, merge ``translations`` branch managed with https://weblate.makina-corpus.net
* Update files *VERSION*, *docs/conf.py* and *docs/changelog.rst* to remove ``+dev`` suffix and increment version (please use semver rules)
* Run ``dch -r -D RELEASED``, update version in the same way and save
* Commit with message 'Release x.y.z' to merge in ``master`` branch before release
* Add git tag X.Y.Z
* Update files *VERSION*, *docs/conf.py* and *docs/changelog.rst* to add ``+dev`` suffix
* Run ``dch -v <version>+dev --no-force-save-on-release`` and save
* Commit with message 'Back to development'
* Push branch and tag
* Add release on Github (copy-paste ``doc/changelog.rst`` paragraph)
* When creating a new release 'x.y.z' on github, Github actions will generate the .deb package file, and publish it on https://packages.geotrek.fr (see ``.circleci/config.yml`` file for details)
