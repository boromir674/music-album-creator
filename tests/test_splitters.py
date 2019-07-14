# -*- coding: utf-8 -*-

import pytest
from music_album_creation.tracks_parsing import StringParser


class TestSplitters:
    @pytest.mark.parametrize("track_line, name, time", [
        ("01. A track - 0:00", "A track", "0:00"),
        ("1 A track - 0:00", "A track", "0:00"),
        ("01 A track - 0:00", "A track", "0:00"),
        ("01. A track - 0:00", "A track", "0:00"),
        ("3.  Uber en Colère - 9:45", "Uber en Colère", '9:45'),
        ("3.  Delta-v - 20:04", 'Delta-v', '20:04'),
        ("3.  Delta-v - 0:00", 'Delta-v', '0:00'),
        ("3  Delta-v - 20:04", 'Delta-v', '20:04'),
        ("3  Delta-v - 0:00", 'Delta-v', '0:00'),
    ])
    def test_tracks_line_parsing(self, track_line, name, time):
        assert StringParser._parse_track_line(track_line) == [name, time]

    @pytest.mark.parametrize("video_title, artist, album, year", [
        ("Alber Jupiter - We Are Just Floating In Space (2019) (New Full Album)", "Alber Jupiter", "We Are Just Floating In Space", "2019"),
        ("My Artist - My Album (2001)", "My Artist", "My Album", "2001"),
        ("Composer A - Metro 2033 (2010)", "Composer A", "Metro 2033", "2010"),
    ])
    def test_youtube_video_title_parsing(self, video_title, artist, album, year):
        assert StringParser.parse_album_info(video_title) == {'artist': artist, 'album': album, 'year': year}

    @pytest.mark.parametrize("tracks_string", [
        ('1. Virtual Funeral - 0:00\n2. Macedonian Lines - 6:46\n3. Melancholy Sadie - 11:30\n4. Bowie’s Last Breath - 16:19\n5. I’m Not A Real Indian (But I Play One On TV) - 20:20\n6. I Make Weird Choices - 23:44'),
        ('1. Virtual Funeral - 0:00\n2. Macedonian Lines - 6:46\n3. Melancholy Sadie - 11:30\n4. Bowie’s Last Breath - 16:19\n5. I’m Not A Real Indian (But I Play One On TV) - 20:20\n6. I Make Weird Choices - 23:44\n'),
        ('1 Virtual Funeral - 0:00\n2 Macedonian Lines - 6:46\n3 Melancholy Sadie - 11:30\n4 Bowie’s Last Breath - 16:19\n5 I’m Not A Real Indian (But I Play One On TV) - 20:20\n6 I Make Weird Choices - 23:44'),
        ('1 Virtual Funeral - 0:00\n2 Macedonian Lines - 6:46\n3 Melancholy Sadie - 11:30\n4 Bowie’s Last Breath - 16:19\n5 I’m Not A Real Indian (But I Play One On TV) - 20:20\n6 I Make Weird Choices - 23:44\n'),
    ])
    def test_tracks_string(self, tracks_string):
        assert StringParser.parse_hhmmss_string(tracks_string) == [['Virtual Funeral', '0:00'],
                                                                   ['Macedonian Lines', '6:46'],
                                                                   ['Melancholy Sadie', '11:30'],
                                                                   ['Bowie’s Last Breath', '16:19'],
                                                                   ["I’m Not A Real Indian (But I Play One On TV)", '20:20'],
                                                                   ['I Make Weird Choices', '23:44']]
