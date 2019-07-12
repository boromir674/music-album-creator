import os
import re
import glob
import click
from mutagen.id3 import ID3, TPE1, TPE2, TRCK, TIT2, TALB, TDRC
from collections import defaultdict

# The main notable classes in mutagen are FileType, StreamInfo, Tags, Metadata and for error handling the MutagenError exception.


class MetadataDealerType(type):

    @staticmethod
    def __parse_year(year):
        if year == '':
            return ''
        c = re.match(r'0*(\d+)', year)
        if not c:
            raise InvalidInputYearError("Input year tag '{}' is invalid".format(year))
        return re.match(r'0*(\d+)', year).group(1)

    def __new__(mcs, name, bases, attributes):
        x = super().__new__(mcs, name, bases, attributes)
        x._filters = defaultdict(lambda: lambda y: y, track_number=lambda y: mcs.__parse_year(y))
        return x


class MetadataDealer(metaclass=MetadataDealerType):

    #############
    # simply add keys and constructor pairs to enrich the support of the API for writting tags/frames to audio files
    # you can use the cls._filters to add a new post processing filter as shown in MetadataDealerType constructor above
    _d = {'artist': TPE1,  # 4.2.1   TPE1    [#TPE1 Lead performer(s)/Soloist(s)]  ; taken from http://id3.org/id3v2.3.0
          #  in clementine temrs, it affects the 'Artist' tab but not the 'Album artist'
          'album_artist': TPE2,  # 4.2.1   TPE2    [#TPE2 Band/orchestra/accompaniment]
          # in clementine terms, it affects the 'Artist' tab but not the 'Album artist'
          'album': TALB,  # 4.2.1   TALB    [#TALB Album/Movie/Show title]
          'year': TDRC  # TDRC (recording time) consolidates TDAT (date), TIME (time), TRDA (recording dates), and TYER (year).

          }

    # supported metadata to try and infer automatically
    _auto_data = [('track_number', TRCK),  # 4.2.1   TRCK    [#TRCK Track number/Position in set]
                  ('track_name', TIT2)]   # 4.2.1   TIT2    [#TIT2 Title/songname/content description]

    _all = dict(_d, **dict(_auto_data))

    reg = re.compile(r'(?:(\d{1,2})(?:[ \t]*[\-\.][ \t]*|[ \t]+)|^)?([\w\'\(\) ’]*[\w)])\.mp3$')  # use to parse track file names like "1. Loyal to the Pack.mp3"

    def set_album_metadata(self, album_directory, track_number=True, track_name=True, artist='', album_artist='', album='', year='', verbose=False):
        self._write_metadata(album_directory, track_number=track_number, track_name=track_name, artist=artist,
                             album_artist=album_artist, album=album, year=str(year), verbose=verbose)

    @classmethod
    def _write_metadata(cls, album_directory, verbose=False, **kwargs):
        files = glob.glob('{}/*.mp3'.format(album_directory))
        if verbose:
            print('FILES\n', list(map(os.path.basename, files)))
        for file in files:
            cls.write_metadata(file, **dict(cls._filter_auto_inferred(cls._infer_track_number_n_name(file), **kwargs),
                                            **{k: kwargs.get(k, '') for k in cls._d.keys()}))

    @classmethod
    def write_metadata(cls, file, verbose=False, **kwargs):
        if not all(map(lambda x: x[0] in cls._all.keys(), kwargs.items())):
            raise RuntimeError("Some of the input keys [{}] used to request the addition of metadata, do not correspoond"
                               " to a tag/frame of the supported [{}]".format(', '.join(kwargs.keys()), ' '.join(cls._d)))
        audio = ID3(file)
        for k, v in kwargs.items():
            if bool(v):
                audio.add(cls._all[k](encoding=3, text=u'{}'.format(cls._filters[k](v))))
                if verbose:
                    print("set '{}' with {}: {}={}".format(file, k, cls._all[k].__name__, cls._filters[k](v)))
        audio.save()

    @classmethod
    def _filter_auto_inferred(cls, d, **kwargs):
        """Given a dictionary (like the one outputted by _infer_track_number_n_name), deletes entries unless it finds them declared in kwargs as key_name=True"""
        for k in cls._auto_data:
            if not kwargs.get(k, False) and k in d:
                del d[k]
        return d

    @classmethod
    def _infer_track_number_n_name(cls, file_name):
        """Call this method to get a dict like {'track_number': 'number', 'track_name': 'name'} from input file name with format like '1. - Loyal to the Pack.mp3'; number must be included!"""
        return {tt[0]: re.search(cls.reg, file_name).group(i+1) for i, tt in enumerate(cls._auto_data)}

class InvalidInputYearError(Exception): pass


@click.command()
@click.option('--album-dir', required=True, help="The directory where a music album resides. Currently only mp3 "
                                                 "files are supported as contents of the directory. Namely only "
                                                 "such files will be apprehended as tracks of the album.")
@click.option('--track_name/--no-track_name', default=True, show_default=True, help='Whether to extract the track names from the mp3 files and write them as metadata correspondingly.')
@click.option('--track_number/--no-track_number', default=True, show_default=True, help='Whether to extract the track numbers from the mp3 files and write them as metadata correspondingly.')
@click.option('--artist', '-a', help="If given, then value shall be used as the TPE1 tag: 'Lead performer(s)/Soloist(s)'.  In the music player 'clementine' it corresponds to the 'Artist' column.")
@click.option('--album_artist', '-aa', help="If given, then value shall be used as the TPE2 tag: 'Band/orchestra/accompaniment'.  In the music player 'clementine' it corresponds to the 'Album artist' column.")
@click.option('--album', '-al', help="If given, then value shall be used as the TALB tag: 'Album/Movie/Show title'.  In the music player 'clementine' it corresponds to the 'Album' column.")
@click.option('--year', 'y', help="If given, then value shall be used as the TDRC tag: 'Recoring time'.  In the music player 'clementine' it corresponds to the 'Year' column.")
def main(album_dir, track_name, track_number, artist, album_artist, album, year):
    md = MetadataDealer()
    md.set_album_metadata(album_dir, track_number=track_number, track_name=track_name, artist=artist, album_artist=album_artist, album=album, year=year, verbose=True)


if __name__ == '__main__':
    main()
