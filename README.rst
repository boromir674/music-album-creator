Music Album Creator - CLI Application
=====================================

Music Album Creator is a CLI application aiming to automate the process of building an offline music digital library.

Featuring

- Automatically downloading and converting to mp3 from youtube
- Segmenting albums into tracks and automatically adding metadata information (ie for 'artist', 'album', 'track_name' fields)
- Cross-platform support (Linux/Windows)
- Cross-python support (Python2.7 or newer)


========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - tests
      - | |travis|
        | |appveyor|
        | |coverage|
        | |docs|
        | |scrutinizer_code_quality|
        | |code_intelligence_status|
    * - package
      - | |version| |wheel| |supported_versions|
        | |commits_since|


.. |docs| image:: https://readthedocs.org/projects/music-album-creator/badge/?version=dev
    :target: https://music-album-creator.readthedocs.io/en/latest/?badge=dev
    :alt: Documentation Status

.. |travis| image:: https://api.travis-ci.org/boromir674/music-album-creator.svg?branch=dev
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/boromir674/music-album-creator

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/0lq9l96dwc6aq33j/branch/dev?svg=true
    :alt: Appveyor Build Status
    :target: https://ci.appveyor.com/project/boromir674/music-album-creator/branch/dev

.. |coverage| image:: https://codecov.io/gh/boromir674/music-album-creator/branch/dev/graph/badge.svg
  :alt: Coverage Status
  :target: https://codecov.io/gh/boromir674/music-album-creator

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

.. |commits_since| image:: https://img.shields.io/github/commits-since/boromir674/music-album-creator/v1.7.5.svg
    :alt: Commits since latest release
    :target: https://github.com/boromir674/music-album-creator/compare/v1.7.5...master


.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/music-album-creator.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/music-album-creator


.. end-badges

* Free software: GNU General Public License v3.0

Installation
============

| Music Album Creator requires the ffmpeg package in order to run. You can download it from https://www.ffmpeg.org/download.html.
| For Linux (Debian) you can simply install it with

::

    sudo apt-get install ffmpeg


To install the Music Album Creator simply do

::

    pip install music-album-creation


Usage
============

To run, simply execute::

    create-album


Documentation
=============


https://music-album-creator.readthedocs.io/


Development
===========

To run all tests run::

    pip install -U tox
    tox -v
