import glob
import logging
import os
import re
from collections import defaultdict

import click
from mutagen.id3 import ID3, TALB, TDRC, TIT2, TPE1, TPE2, TRCK

from music_album_creation.tracks_parsing import StringParser

# The main notable classes in mutagen are FileType, StreamInfo, Tags, Metadata and for error handling the MutagenError exception.


logger = logging.getLogger(__name__)


class MetadataDealerType(object):
    _filters = defaultdict(
        lambda: lambda y: y, track_number=lambda y: MetadataDealerType._parse_year(y)
    )

    @classmethod
    def _parse_year(cls, year):
        if year == '':
            return ''
        c = re.match(r'0*(\d+)', year)
        if not c:
            raise InvalidInputYearError("Input year tag '{}' is invalid".format(year))
        return c.group(1)


class MetadataDealer(MetadataDealerType):
    #############
    # simply add keys and constructor pairs to enrich the support of the API for writting tags/frames to audio files
    # you can use the cls._filters to add a new post processing filter as shown in MetadataDealerType constructor above
    _d = {
        'artist': TPE1,  # 4.2.1   TPE1    [#TPE1 Lead performer(s)/Soloist(s)]  ; taken from http://id3.org/id3v2.3.0
        #  in clementine temrs, it affects the 'Artist' tab but not the 'Album artist'
        'album_artist': TPE2,  # 4.2.1   TPE2    [#TPE2 Band/orchestra/accompaniment]
        # in clementine terms, it affects the 'Artist' tab but not the 'Album artist'
        'album': TALB,  # 4.2.1   TALB    [#TALB Album/Movie/Show title]
        'year': TDRC,  # TDRC (recording time) consolidates TDAT (date), TIME (time), TRDA (recording dates), and TYER (year).
    }

    # supported metadata to try and infer automatically
    _auto_data = [
        ('track_number', TRCK),  # 4.2.1   TRCK    [#TRCK Track number/Position in set]
        ('track_name', TIT2),
    ]  # 4.2.1   TIT2    [#TIT2 Title/songname/content description]

    _all = dict(_d, **dict(_auto_data))

    @classmethod
    def set_album_metadata(
        cls,
        album_directory,
        track_number=True,
        track_name=True,
        artist='',
        album_artist='',
        album='',
        year='',
    ):
        cls._write_metadata(
            album_directory,
            track_number=track_number,
            track_name=track_name,
            artist=artist,
            album_artist=album_artist,
            album=album,
            year=str(year),
        )

    @classmethod
    def _write_metadata(cls, album_directory, **kwargs):
        files = glob.glob('{}/*.mp3'.format(album_directory))
        logger.info("Album directory: {}".format(album_directory))
        for file in files:
            logger.info("File: {}".format(os.path.basename(file)))
            cls.write_metadata(
                file,
                **dict(
                    cls._filter_auto_inferred(
                        StringParser().parse_track_number_n_name(file), **kwargs
                    ),
                    **{k: kwargs.get(k, '') for k in cls._d.keys()}
                )
            )

    @classmethod
    def write_metadata(cls, file, **kwargs):
        if not all(map(lambda x: x[0] in cls._all.keys(), kwargs.items())):
            raise RuntimeError(
                "Some of the input keys [{}] used to request the addition of metadata, do not correspond"
                " to a tag/frame of the supported [{}]".format(
                    ', '.join(kwargs.keys()), ' '.join(cls._d)
                )
            )
        audio = ID3(file)
        for metadata_name, v in kwargs.items():
            if bool(v):
                audio.add(
                    cls._all[metadata_name](
                        encoding=3, text=u'{}'.format(cls._filters[metadata_name](v))
                    )
                )
                logger.info(
                    " {}: {}={}".format(
                        metadata_name,
                        cls._all[metadata_name].__name__,
                        cls._filters[metadata_name](v),
                    )
                )
            else:
                logger.warning(
                    "Skipping metadata '{}::'{}' because bool({}) == False".format(
                        metadata_name, cls._all[metadata_name].__name__, v
                    )
                )
        audio.save()

    @classmethod
    def _filter_auto_inferred(cls, d, **kwargs):
        """Given a dictionary (like the one outputted by _infer_track_number_n_name), deletes entries unless it finds them declared in kwargs as key_name=True"""
        for k in cls._auto_data:
            if not kwargs.get(k, False) and k in d:
                del d[k]
        return d


class InvalidInputYearError(Exception):
    pass


@click.command()
@click.option(
    '--album-dir',
    required=True,
    help="The directory where a music album resides. Currently only mp3 "
    "files are supported as contents of the directory. Namely only "
    "such files will be apprehended as tracks of the album.",
)
@click.option(
    '--track_name/--no-track_name',
    default=True,
    show_default=True,
    help='Whether to extract the track names from the mp3 files and write them as metadata correspondingly.',
)
@click.option(
    '--track_number/--no-track_number',
    default=True,
    show_default=True,
    help='Whether to extract the track numbers from the mp3 files and write them as metadata correspondingly.',
)
@click.option(
    '--artist',
    '-a',
    help="If given, then value shall be used as the TPE1 tag: 'Lead performer(s)/Soloist(s)'.  In the music player 'clementine' it corresponds to the 'Artist' column.",
)
@click.option(
    '--album_artist',
    '-aa',
    help="If given, then value shall be used as the TPE2 tag: 'Band/orchestra/accompaniment'.  In the music player 'clementine' it corresponds to the 'Album artist' column.",
)
@click.option(
    '--album',
    '-al',
    help="If given, then value shall be used as the TALB tag: 'Album/Movie/Show title'.  In the music player 'clementine' it corresponds to the 'Album' column.",
)
@click.option(
    '--year',
    'y',
    help="If given, then value shall be used as the TDRC tag: 'Recoring time'.  In the music player 'clementine' it corresponds to the 'Year' column.",
)
def main(album_dir, track_name, track_number, artist, album_artist, album, year):
    md = MetadataDealer()
    md.set_album_metadata(
        album_dir,
        track_number=track_number,
        track_name=track_name,
        artist=artist,
        album_artist=album_artist,
        album=album,
        year=year,
    )


if __name__ == '__main__':
    main()
