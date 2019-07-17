# -*- coding: utf-8 -*-

import pytest
from music_album_creation.tracks_parsing import StringParser, Timestamp


@pytest.fixture(scope='module')
def track_durations():
    return ["0:12", "0:38", "0:20", "0:25", "0:10", "0:30", "1:00"]


@pytest.fixture(scope='module')
def track_timestamps():
    return ["0:00", "0:12", "0:50", "1:10", "1:35", "1:45", "2:15"]

@pytest.fixture(scope='module')
def delimeters1():
    return ['. ', ' - ', '.  ', '  -  ', '.   ']

@pytest.fixture(scope='module')
def track_names():
    return ['a,b', 'SOS: edw', 'Ζόμπι, το Ξύπνημα των Νεκρών', "Uber en Colère", "Delta-v", "Bowie’s Last Breath", "I’m Not A Real Indian (But I Play One On TV)", '24', 'Στενές Επαφές Τρίτου Τύπου (Disco Tsoutsouni)', 'SOS: Πεντάγωνο καλεί Μόσχα (Νύχτες της Μόσχας)', 'Οικογενειακή Συνωμοσία']

@pytest.fixture(scope='module')
def delimeters2():
    return [' ', ' - ', '  -  ', '   -   ', ' -    ']

def build_string(dels1, names, dels2, hhmmss_list):
    return '\n'.join(['{}{}{}{}{}'.format(i+1, dels1[i % len(dels1)], x[0], dels2[i % len(dels2)], x[1]) for i, x in enumerate(zip(names, hhmmss_list))])

@pytest.fixture(scope='module')
def timestamps_info_string(delimeters1, track_names, delimeters2, track_timestamps):
    return build_string(delimeters1, track_names, delimeters2, track_timestamps)

@pytest.fixture(scope='module')
def durations_info_string(delimeters1, track_names, delimeters2, track_durations):
    return build_string(delimeters1, track_names, delimeters2, track_durations) + '\n'


class TestSplitters:

    @pytest.mark.parametrize("video_title, artist, album, year", [
        ("Alber Jupiter - We Are Just Floating In Space (2019) (New Full Album)", "Alber Jupiter", "We Are Just Floating In Space", "2019"),
        ("My Artist - My Album (2001)", "My Artist", "My Album", "2001"),
        ("Composer A - Metro 2033 (2010)", "Composer A", "Metro 2033", "2010"),
    ])
    def test_youtube_video_title_parsing(self, video_title, artist, album, year):
        assert StringParser.parse_album_info(video_title) == {'artist': artist, 'album': album, 'year': year}

    @pytest.mark.parametrize("track_file, track_number, track_name", [
        ("Thievery Corporation/The Cosmic Game (2005)/14 - The Supreme Illusion (Feat- Gunjan).mp3", '14', 'The Supreme Illusion (Feat- Gunjan)'),
        ("Monster Magnet/Dopes to Infinity (Single) 1995/02 - Forbidden Planet.mp3", '02', 'Forbidden Planet'),
        ("Monster Magnet/Greatest Hits 2003/02 - Medicine.mp3", '02', 'Medicine'),
        ("Porcupine Tree/On The Sunday Of Life/07 - Message Form A Self-Destructing Turnip.mp3", '07', 'Message Form A Self-Destructing Turnip'),
        ("Rotor/Rotor 2001/06 A Madrugada.mp3", '06', 'A Madrugada'),
        ("Karma To Burn/Arc Stanton 2014/02 56.mp3", '02', '56'),
        ("Cesaria Evora/Cesaria Evora - Cabo Verde/06-Mar e Morada De Sodade.mp3", '06', 'Mar e Morada De Sodade'),
        ("Sungrazer/Sungrazer - Mirador (2011)/06.Mirador.mp3", '06', 'Mirador'),
        ("SadhuS (The Smoking Community)/Sadhus The smoking community/06 Bampoola.mp3", '06', 'Bampoola'),
        ("Remember Me - Original Soundtrack (2013)/12. The Ego Room.mp3", '12', 'The Ego Room'),
        ("Queens of the Stone Age/Like a Clockwork/02 I Sat By the Ocean.mp3", '02', 'I Sat By the Ocean'),
        ("Ill Nino/[2010] Dead New World/05 - Bleed Like You.mp3", '05', 'Bleed Like You'),
        ("Urban Dance Squad/Urban Dance Squad - Life 'n Perspectives of a Genuine Crossover/03. Life 'n Perspectives I.mp3", '03', "Life 'n Perspectives I"),
        ("Cesaria Evora/Cesaria Evora - Cafe Atlantico/06-Carnaval De Sao Vicente.mp3", '06', 'Carnaval De Sao Vicente'),
        ("Dala Sun/Sala Dun (2010)/04 - Fuck It Away.mp3", '04', 'Fuck It Away'),
        ("In This Moment/Blood (2012)/01- Rise With Me.mp3", '01', 'Rise With Me'),
    ])
    def test_mp3_files_parsing(self, track_file, track_number, track_name):
        assert StringParser.parse_track_number_n_name(track_file) == {'track_number': track_number, 'track_name': track_name}

    def test_parsing_timestamps_tracks_info(self, timestamps_info_string, track_names, track_timestamps):
        assert StringParser.parse_hhmmss_string(timestamps_info_string) == [[x, y] for x, y in zip(track_names, track_timestamps)]

    def test_parsing_durations_tracks_info(self, durations_info_string, track_names, track_durations):
        assert StringParser.parse_hhmmss_string(durations_info_string) == [[x, y] for x, y in zip(track_names, track_durations)]

    def test_durations_list_converion(self, track_durations, track_timestamps):
        assert [int(Timestamp(_[1])) for _ in StringParser.duration_data_to_timestamp_data([['a', x] for x in track_durations])] == [int(Timestamp(_)) for _ in track_timestamps]

    def test_convert_to_timestamps(self, durations_info_string, track_timestamps):
        assert list(map(Timestamp, StringParser.convert_to_timestamps(durations_info_string))) == list(map(Timestamp, track_timestamps))

def test_timestamp():
    assert Timestamp('45:17') <= Timestamp('50:00') and Timestamp('0:0:34') < Timestamp('1:34')
    assert Timestamp('1:0:34') >= Timestamp('56:36') and Timestamp('1:1:34') > Timestamp('0:4')
    assert Timestamp('12') == Timestamp('0:12') == Timestamp('00:0:12') == Timestamp('00:12')
    assert Timestamp('9') == Timestamp('0:09') == Timestamp('09') == Timestamp('00:09') == Timestamp('00:9')
    assert Timestamp('0:0:9') == Timestamp('0:0:09') == Timestamp('00:0:09') == Timestamp('0:0:09') == Timestamp('09')
    assert hash(Timestamp('12')) == hash(Timestamp('0:12')) == hash(Timestamp('00:0:12')) == hash(Timestamp('00:12'))
    assert hash(Timestamp('9')) == hash(Timestamp('0:09')) == hash(Timestamp('09')) == hash(Timestamp('00:09')) == hash(Timestamp('00:9'))
    assert hash(Timestamp('0:0:9')) == hash(Timestamp('0:0:09')) == hash(Timestamp('00:0:09')) == hash(Timestamp('0:0:09')) == hash(Timestamp('09'))

    assert int(Timestamp('23:57') - Timestamp('16:43')) == 434
