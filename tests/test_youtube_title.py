import pytest


@pytest.fixture
def given(scope='module'):
    from music_album_creation.web_parsing import video_title
    return type('Given', (), {
        'compute_title': video_title
    })

@pytest.mark.network_bound
@pytest.mark.parametrize('url, expected_title', [
    ('https://www.youtube.com/watch?v=Q3dvbM6Pias', 'Rage Against The Machine - Testify (Official HD Video)'),
    ('https://www.youtube.com/watch?v=4U0hCmAzRsg', 'Planet of Zeus - Loyal to the Pack (Official Lyric Video)'),
])
def test_expected_video_title_is_fetched_from_url(url, expected_title, given):
    assert given.compute_title(url) == expected_title
