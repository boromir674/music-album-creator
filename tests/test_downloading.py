import os
from time import sleep
import pytest

from music_album_creation.downloading import YoutubeDownloader, InvalidUrlError, UnavailableVideoError, TooManyRequestsError, CertificateVerificationError


@pytest.fixture(scope='module')
def youtube():
    return YoutubeDownloader


class TestYoutubeDownloader:
    NON_EXISTANT_YOUTUBE_URL = 'https://www.youtube.com/watch?v=alpharegavgav'
    INVALID_URL = 'gav'
    duration = '3:43'
    duration_in_seconds = 223


    def attemp_download(self, url, times=10, sleep_seconds=1):
        i = 0
        while i < times:
            try:
                YoutubeDownloader.download(url, '/tmp/', spawn=False, verbose=False, supress_stdout=True)
                break
            except TooManyRequestsError as e:
                print(e)
                i = times

    def test_downloading_false_youtube_url(self, youtube):
        suppress_certificate_validation = False
        i = 0
        with pytest.raises(UnavailableVideoError):
            while i < 10:
                try:
                    youtube.download(self.NON_EXISTANT_YOUTUBE_URL, '/tmp/', spawn=False, verbose=False, supress_stdout=True, suppress_certificate_validation=suppress_certificate_validation)
                except CertificateVerificationError as e:
                    print('Attempt {}: {}'.format(i + 1, e))
                    suppress_certificate_validation = True
                    sleep(0.3)
                except TooManyRequestsError as e:
                    print('Attempt {}: {}'.format(i+1, e))
                    sleep(1)
                i += 1

    def test_downloading_invalid_url(self, youtube):
        with pytest.raises(InvalidUrlError):
            youtube.download(self.INVALID_URL, '/tmp/', spawn=False, verbose=False, supress_stdout=True)

    @pytest.mark.parametrize("url, target_file", [('https://www.youtube.com/watch?v=Q3dvbM6Pias', 'Rage Against The Machine - Testify')])
    def test_downloading_valid_url(self, url, target_file, youtube):
        suppress_certificate_validation = False
        i = 0
        while i < 10:
            try:
                youtube.download(url, '/tmp', spawn=False, verbose=False, supress_stdout=True, suppress_certificate_validation=suppress_certificate_validation)
                assert os.path.isfile('/tmp/' + target_file + '.mp3')
                break
            except TooManyRequestsError as e:
                print(e)
                sleep(1)
            except CertificateVerificationError as e:
                suppress_certificate_validation = True
                print(e)
                sleep(0.3)
            i += 1
