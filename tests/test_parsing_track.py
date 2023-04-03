import pytest


@pytest.fixture(params=(
    ('01. track_name - 00:00', ('track_name', '00:00')),
    ('01,   1312 - 00:00:00', ('1312', '00:00:00')),
    ('2  -  Faith in Physics - 12:43', ('Faith in Physics', '12:43')),
    ('23   -   Ντίσκο Τσουτσούνι - 1:00:00', ('Ντίσκο Τσουτσούνι', '1:00:00')),
    ('2.  Man vs. God - 0:07', ('Man vs. God', '0:07')),
))
def parsable_track_lines(request):
    """A track line (str) that we can parse."""
    return {
        'track_line': request.param[0],
        'expected_track_name': request.param[1][0],
        'expected_parsed_time': request.param[1][1],
    }


def test_parsing_track_line(parsable_track_lines):
    """Test parsing a track line."""
    from typing import List

    from music_album_creation.tracks_parsing import StringParser
    parser = StringParser()
    track_name, parsed_time = parser._parse_track_line(parsable_track_lines['track_line'])
    assert track_name == parsable_track_lines['expected_track_name']
    assert parsed_time == parsable_track_lines['expected_parsed_time']
