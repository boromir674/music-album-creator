import pytest


@pytest.fixture
def valid_youtube_videos():
    """Youtube video urls and their expected mp3 name to be 'downloaded'.

    Note:
        Maintain this fixture in cases such as a youtube video title changing
        over time, or a youtube url ceasing to exist.

    Returns:
        [type]: [description]
    """
    from collections import namedtuple
    YoutubeVideo = namedtuple('YoutubeVideo', ['url', 'video_title'])
    return {YoutubeVideo(url, video_title) for url, video_title in {
        ('https://www.youtube.com/watch?v=jJkF3I5cBAc', '10 seconds countdown (video test)'),
        # ('https://www.youtube.com/watch?v=Q3dvbM6Pias', 'Rage Against The Machine - Testify (Official HD Video)'),
    }}
