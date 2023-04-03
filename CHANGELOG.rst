=========
Changelog
=========

Maintainance Release for Music Album Creation.

- change **download backend** from `youtube-dl` to lightwight `pytube`
- change **interactive dialogs** backend from legacy `pyinquirer` to `questionary`

1.4.0 (2023-04-03)
==================

Changes
^^^^^^^

maintainance
""""""""""""
- retire prediction service due to legacy dependency with scikit version & pickeld model weights

build
"""""
- update python dependencies using poetry version 1.4.0

ci
--
- migrate from Travis to Github Actions
- full CI/CD pipeline


1.3.2 (2019-11-03)
==================

documentation
^^^^^^^^^^^^^
- add structured documentation and host it in readthedocs.io

1.3.1 (2019-11-02)
==================
- fix for python2.7

1.3.0 (2019-11-01)
==================

feature
^^^^^^^
- support python2.7

1.2.1 (2019-10-14)
==================

Changes
^^^^^^^

- Fix identation error


1.2.0 (2019-10-13)
==================

Changes
^^^^^^^

- Write integration test
- Fix 3 minor security issues and 2 medium
- Implement alternative method to retrieve album name
- Improve 'front-end' architecture


1.1.4 (2019-07-28)
==================

Changes
^^^^^^^

- Fix track segmentation in linux systems.
- Settle for 9 minor and 3 medium issues of security severity


1.1.3 (2019-07-27)
==================

Changes
^^^^^^^

- Improve security


1.1.1 (2019-07-21)
==================

Changes
^^^^^^^

- Enable Appveyor CI build trigerring for windows platform.
- Use tox as 'front-end' for testing (locally/Travis-Ci/Appveyor)
- Improve test coverage



1.0.7a (2019-07-08)
==================

Changes
^^^^^^^

- Add a universal wheel


1.0.7 (2019-07-08)
==================

Changes:
^^^^^^^^

Initial release.
