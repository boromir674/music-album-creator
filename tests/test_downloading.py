import os
import pytest

from music_album_creation.downloading import YoutubeDownloader, InvalidUrlError, UnavailableVideoError, CertificateVerificationError


@pytest.fixture(scope='module')
def download():
    return lambda url, target_directory, times, suppress_certificate_validation: YoutubeDownloader.download_times(url,
                                                                                                                  target_directory,
                                                                                                                  times=10,
                                                                                                                  spawn=False,
                                                                                                                  verbose=False,
                                                                                                                  supress_stdout=True,
                                                                                                                  suppress_certificate_validation=suppress_certificate_validation,
                                                                                                                  delay=0.8)

@pytest.fixture(scope='module')
def download_trials():
    return 15



class TestYoutubeDownloader:
    NON_EXISTANT_YOUTUBE_URL = 'https://www.youtube.com/watch?v=alpharegavgav'
    INVALID_URL = 'gav'
    duration = '3:43'
    duration_in_seconds = 223

    def download_trial(self, url, directory, download_callback, nb_trials):
        suppress_certificate_validation = False
        try:
            download_callback(url, directory, 1, suppress_certificate_validation)
        except CertificateVerificationError:
            download_callback(url, directory, nb_trials, True)

    @pytest.mark.parametrize("url, target_file", [
        ('https://www.youtube.com/watch?v=Q3dvbM6Pias', 'Rage Against The Machine - Testify (Official Video).mp3')])
    def test_downloading_valid_youtube_url(self, url, target_file, tmpdir, download, download_trials):
        target_directory = str(tmpdir.mkdir('youtubedownloads'))
        self.download_trial(url, target_directory, download, download_trials)
        assert os.path.isfile(os.path.join(target_directory, target_file))

    def test_downloading_false_youtube_url(self, download, download_trials):
        with pytest.raises(UnavailableVideoError):
            self.download_trial(self.NON_EXISTANT_YOUTUBE_URL, '/tmp', download, download_trials)

    def test_downloading_invalid_url(self, download):
        with pytest.raises(InvalidUrlError):
            download(self.INVALID_URL, '/tmp/', 1, False)
