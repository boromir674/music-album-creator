import os
from glob import glob

import pytest
from music_album_creation.downloading import (CertificateVerificationError,
                                              CMDYoutubeDownloader,
                                              InvalidUrlError,
                                              UnavailableVideoError)
from music_album_creation.web_parsing import video_title


@pytest.fixture(scope='module')
def download():
    youtue = CMDYoutubeDownloader()
    return lambda url, target_directory, times, suppress_certificate_validation: youtue.download_trials(url, target_directory,
                                                                                                        times=10,
                                                                                                        suppress_certificate_validation=suppress_certificate_validation,
                                                                                                        delay=0.8)
@pytest.fixture(scope='module')
def download_trials():
    return 15


NON_EXISTANT_YOUTUBE_URL = 'https://www.youtube.com/watch?v=alpharegavgav'
INVALID_URL = 'gav'
duration = '3:43'
duration_in_seconds = 223

@pytest.fixture
def download_trial():
    def _download_trial(url, directory, download_callback, nb_trials):
        try:
            download_callback(url, directory, times=1, suppress_certificate_validation=False)
        except CertificateVerificationError:
            download_callback(url, directory, times=nb_trials, suppress_certificate_validation=True)
    return _download_trial

# @pytest.mark.parametrize("url, target_file", [
#     ('https://www.youtube.com/watch?v=Q3dvbM6Pias', 'Rage Against The Machine - Testify (Official Video).mp3')])
@pytest.mark.network_bound
def test_downloading_valid_youtube_url(download_trial, tmpdir, download, download_trials, valid_youtube_videos):
    target_directory = str(tmpdir.mkdir('youtubedownloads'))
    for youtube_video in valid_youtube_videos:
        download_trial(youtube_video.url, target_directory, download, download_trials)
        assert len(glob('{}/*'.format(target_directory))) == 1
        assert os.path.isfile(os.path.join(target_directory, f'{youtube_video.video_title}.mp3')) or os.path.isfile(os.path.join(target_directory, '_.mp3'))

@pytest.mark.network_bound
def test_downloading_false_youtube_url(download_trial, download, download_trials):
    with pytest.raises(UnavailableVideoError):
        download_trial(NON_EXISTANT_YOUTUBE_URL, '/tmp', download, download_trials)

@pytest.mark.network_bound
def test_downloading_invalid_url(download):
    with pytest.raises(InvalidUrlError):
        download(INVALID_URL, '/tmp/', 1, False)
