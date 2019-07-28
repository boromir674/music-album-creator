"""This module tests writting metadata to audio files . It tests both valid and invalid values for the 'year' (TDRC) field"""
import os
from glob import glob

import pytest
from mutagen.id3 import ID3

from music_album_creation.metadata import MetadataDealer as MD
from music_album_creation.tracks_parsing import StringParser


@pytest.fixture(scope='module')
def test_album_dir():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data/album_0/')


@pytest.fixture(scope='module')
def album_info():
    return {'artist': ['ratm', 'TPE1'],
            'album-artist': ['ratm', 'TPE2'],
            'album': ['renegades', 'TALB'],
            'year': ['2000', 'TDRC']}

@pytest.fixture(scope='module')
def tags_from_file_name():
    return {'track_number': {'tag': 'TRCK', 'parser': lambda x: str(int(x))},  # 4.2.1   TRCK    [#TRCK Track number/Position in set]
            'track_name': {'tag': 'TIT2'}}   # 4.2.1   TIT2    [#TIT2 Title/songname/content description]


@pytest.mark.parametrize("year", [
    ('2000'),
    (''),
    pytest.param('a_year', marks=pytest.mark.xfail)
])
def test_writting_album_metadata(test_album_dir, album_info, tags_from_file_name, year):
    MD.set_album_metadata(test_album_dir, track_number=True, track_name=True, artist=album_info['artist'][0],
                          album_artist=album_info['album-artist'][0], album=album_info['album'][0], year=year, verbose=True)
    for file_path in glob(test_album_dir + '/*'):
        c = StringParser.parse_track_number_n_name(os.path.basename(file_path))
        audio = ID3(file_path)
        # this is tru because when trying to set the year metadata with '' the tag s do not change and so remain to the '2000' value set in the first test in line
        # assert all([str(audio.get(album_info[k][1]) == album_info[k][0] for k in ['artist', 'album-artist', 'album'])]) and str(audio.get(album_info['year'][1])) == album_info
        # for k, v in tags_from_file_name.items():
        #     print("TAG SET: {}={}, requested: {}={}".format(v, str(audio.get(v)), k, c[k]))
        assert all([str(audio.get(album_info[k][1]) == album_info[k][0] for k in album_info.keys())]) and all([str(audio.get(data['tag'])) == data.get('parser', lambda x: x)(c[k]) for k, data in tags_from_file_name.items()])
