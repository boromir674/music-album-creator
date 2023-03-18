import os
from glob import glob

import pytest
from music_album_creation.downloading import (
    CertificateVerificationError,
                                              CMDYoutubeDownloader,
                                              )
from music_album_creation.web_parsing import video_title


@pytest.fixture(scope='module')
def download():
    youtue = CMDYoutubeDownloader()
    return lambda url, target_directory, times, suppress_certificate_validation: youtue.download_trials(
        url, target_directory,
        times=times,
        suppress_certificate_validation=suppress_certificate_validation,
        delay=0.8)


@pytest.fixture(scope='module')
def nb_download_trials():
    return 3


NON_EXISTANT_YOUTUBE_URL = 'https://www.youtube.com/watch?v=alpharegavgavasdfsh'
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
def test_downloading_valid_youtube_url(download_trial, tmp_path_factory, download, nb_download_trials):
    target_directory = tmp_path_factory.mktemp("youtubedownloads")
    target_directory = str(target_directory)
    # for youtube_video in [('https://www.youtube.com/watch?v=UO2JIPOYhIk&list=OLAK5uy_k80e1ODmXyVy6K25BL6PS4wCFg1hwjkX0&index=3', 'The Witch')]:
    for youtube_video in [
        ('https://www.youtube.com/watch?v=bj1JRuyYeco',
        '20 Second Timer (Minimal)')]:
        
        url, title_name = youtube_video
        download_trial(url, target_directory, download, nb_download_trials)
        assert len(glob('{}/*'.format(target_directory))) == 2

        assert os.path.isfile(os.path.join(target_directory, f'{title_name}.webm'))
        assert os.path.isfile(os.path.join(target_directory, f'{title_name}.mp4'))


@pytest.mark.network_bound
def test_downloading_false_youtube_url(download_trial, download, nb_download_trials):
    from pytube.exceptions import VideoUnavailable
    with pytest.raises(VideoUnavailable):
        download_trial(NON_EXISTANT_YOUTUBE_URL, '/tmp', download, nb_download_trials)

@pytest.mark.network_bound
def test_downloading_invalid_url(download):
    from pytube.exceptions import RegexMatchError
    with pytest.raises(RegexMatchError):
        download(INVALID_URL, '/tmp/', 1, False)
