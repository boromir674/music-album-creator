import os
import pytest

from music_album_creation.downloading import YoutubeDownloader, InvalidUrlError, UnavailableVideoError


@pytest.fixture(scope='module')
def youtube():
    return YoutubeDownloader


class TestYoutubeDownloader:
    NON_EXISTANT_YOUTUBE_URL = 'https://www.youtube.com/watch?v=alpharegavgav'
    INVALID_URL = 'gav'
    duration = '3:43'
    duration_in_seconds = 223

    def test_downloading_false_youtube_url(self, youtube):
        with pytest.raises(UnavailableVideoError):
            youtube.download(self.NON_EXISTANT_YOUTUBE_URL, '/tmp/', spawn=False, verbose=False, supress_stdout=True)

    def test_downloading_invalid_url(self, youtube):
        with pytest.raises(InvalidUrlError):
            youtube.download(self.INVALID_URL, '/tmp/', spawn=False, verbose=False, supress_stdout=True)

    @pytest.mark.parametrize("url, target_file", [('https://www.youtube.com/watch?v=Q3dvbM6Pias', 'Rage Against The Machine - Testify')])
    def test_downloading_valid_url(self, url, target_file, youtube):
        youtube.download(url, '/tmp', spawn=False, verbose=False, supress_stdout=True)
        assert os.path.isfile('/tmp/'+target_file+'.mp3')