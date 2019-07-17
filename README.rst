Music Album Creator - CLI Application
=====================================

Music Album Creator is a cli application aiming to automate the process of building an offline music digital library.


========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - tests
      - | |travis|
        | |coveralls|
        | |scrutinizer_code_quality|
        | |code_intelligence_status|
    * - package
      - | |version| |wheel| |supported_versions|
        | |commits_since|


.. |docs| image:: https://readthedocs.org/projects/music-album-creator/badge/?style=flat
    :target: https://readthedocs.org/projects/music-album-creation
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/boromir674/music-album-creator.svg?branch=dev
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/boromir674/music-album-creator

.. |coveralls| image:: https://coveralls.io/repos/github/boromir674/music-album-creator/badge.svg?branch=dev
    :alt: Coverage Status
    :target: https://coveralls.io/github/boromir674/music-album-creator?branch=dev

.. |scrutinizer_code_quality| image:: https://scrutinizer-ci.com/g/boromir674/music-album-creator/badges/quality-score.png?b=dev
    :alt: Code Quality
    :target: https://scrutinizer-ci.com/g/boromir674/music-album-creator/?branch=dev

.. |code_intelligence_status| image:: https://scrutinizer-ci.com/g/boromir674/music-album-creator/badges/code-intelligence.svg?b=dev
    :alt: Code Intelligence
    :target: https://scrutinizer-ci.com/code-intelligence

.. |version| image:: https://img.shields.io/pypi/v/music-album-creation.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/music-album-creation

.. |wheel| image:: https://img.shields.io/pypi/wheel/music-album-creation.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/music-album-creation

.. |supported_versions| image:: https://img.shields.io/pypi/pyversions/music-album-creation.svg
    :alt: Supported versions
    :target: https://pypi.org/project/music-album-creation

.. |commits_since| image:: https://img.shields.io/github/commits-since/boromir674/music-album-creator/v1.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/boromir674/music-album-creator/compare/v1.1.0...master


.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/music-album-creator.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/music-album-creator


.. end-badges

A CLI application intending to automate offline music library building.

* Free software: GNU General Public License v3.0

Installation
============

::

    pip install music-album-creator


Usage
============

To run, simply execute::

    create-album


Documentation
=============


https://music-album-creator.readthedocs.io/


Development
===========

To run the all tests run::

    tox
