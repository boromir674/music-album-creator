"""Run `python -m create_album`.

Allow invoking Music Album Creation CLI as a python module with the
`python -m create_album` command.

This is an alternative to directly invoking the cli that uses python as the
"entrypoint".
"""
from __future__ import absolute_import

from music_album_creation.create_album import main

if __name__ == "__main__":  # pragma: no cover
    main(prog_name="music-album-creation")
