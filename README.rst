Music Album Creator - CLI Application
=====================================

Music Album Creator is a cli application aiming to automate the process of building an offline music library.


========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis|
        | |coveralls|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/music-album-creator/badge/?style=flat
    :target: https://readthedocs.org/projects/music-album-creator
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/boromir674/music-album-creator.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/boromir674/music-album-creator

.. |coveralls| image:: https://coveralls.io/repos/boromir674/music-album-creator/badge.svg?branch=master&service=github
    :alt: Coverage Status
    :target: https://coveralls.io/r/boromir674/music-album-creator

.. |version| image:: https://img.shields.io/pypi/v/music-album-creator.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/music-album-creator

.. |commits-since| image:: https://img.shields.io/github/commits-since/boromir674/music-album-creator/v0.svg
    :alt: Commits since latest release
    :target: https://github.com/boromir674/music-album-creator/compare/v0...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/music-album-creator.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/music-album-creator

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/music-album-creator.svg
    :alt: Supported versions
    :target: https://pypi.org/project/music-album-creator

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/music-album-creator.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/music-album-creator


.. end-badges

A CLI application intending to automate offline music library building.

* Free software: Apache Software License 2.0

Installation
============

::

    pip install music-album-creator

Documentation
=============


https://music-album-creator.readthedocs.io/


Development
===========

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
