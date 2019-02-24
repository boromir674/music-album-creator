import os
import pytest

from downloading import YoutubeDownloader, WrongYoutubeUrl



@pytest.fixture(scope='module')
def downloader():
    return YoutubeDownloader()


class TestYoutubeDownloader:
    NON_EXISTANT_YOUTUBE_URL = 'https://www.youtube.com/watch?v=alpharegavgav'
    duration = '3:43'
    duration_in_seconds = 223

    def test_downloading_false_url(self, downloader):
        with pytest.raises(WrongYoutubeUrl):
            downloader.download(self.NON_EXISTANT_YOUTUBE_URL, '/tmp/', spawn=False, verbose=False, supress_stdout=True)

    @pytest.mark.parametrize("url, target_file", [('https://www.youtube.com/watch?v=Q3dvbM6Pias', 'Rage Against The Machine - Testify')])
    def test_downloading_valid_url(self, url, target_file, downloader):
        downloader.download(url, '/tmp', spawn=False, verbose=False, supress_stdout=True)
        assert os.path.isfile('/tmp/'+target_file+'.mp3')