import os
from glob import glob

import pytest

from music_album_creation.downloading import (
    CertificateVerificationError,
    CMDYoutubeDownloader,
)
from music_album_creation.web_parsing import video_title

NON_EXISTANT_YOUTUBE_URL = 'https://www.youtube.com/watch?v=alpharegavgavasdfsh'
INVALID_URL = 'gav'
duration = '3:43'
duration_in_seconds = 223


@pytest.fixture(scope='module')
def download():
    youtue = CMDYoutubeDownloader()
    return lambda url, target_directory, times, suppress_certificate_validation: youtue.download_trials(
        url,
        target_directory,
        times=times,
        suppress_certificate_validation=suppress_certificate_validation,
        delay=0.8,
    )


@pytest.mark.network_bound
@pytest.mark.parametrize('url, target_file', [
    (
        'https://www.youtube.com/watch?v=Q3dvbM6Pias',
        'Rage Against The Machine - Testify (Official HD Video).mp4'
    ),
    (
        'https://www.youtube.com/watch?v=bj1JRuyYeco',
        '20 Second Timer (Minimal).webm'
    ),
])
def test_downloading_valid_youtube_url(
    url, target_file,
    tmp_path_factory
):
    from pathlib import Path

    from music_album_creation.downloading import CMDYoutubeDownloader

    target_directory = tmp_path_factory.mktemp("youtubedownloads")
    target_directory = str(target_directory)

    expected_file_name = target_file

    youtube = CMDYoutubeDownloader()
    downloaded_file = youtube.download_trials(
        url,
        target_directory,
        times=5,
        delay=0.8,
    )

    downloaded_path: Path = Path(str(downloaded_file))

    # THEN File has been downloaded
    assert downloaded_path.exists()
    assert downloaded_path.is_file()

    # AND FILE has the expected name
    assert downloaded_path.name == expected_file_name
    assert downloaded_path.suffix == '.' + expected_file_name.split('.')[-1]


# Test that expected Exceptions are fired up

@pytest.mark.network_bound
def test_downloading_false_youtube_url(tmp_path_factory):
    from pytube.exceptions import VideoUnavailable

    from music_album_creation.downloading import CMDYoutubeDownloader
    youtube = CMDYoutubeDownloader()

    with pytest.raises(VideoUnavailable):
        youtube.download_trials(
            NON_EXISTANT_YOUTUBE_URL,
            str(tmp_path_factory.mktemp("unit-test")),
            times=3,
            delay=0.8,
        )


@pytest.mark.network_bound
def test_downloading_invalid_url(download, tmp_path_factory):
    from pytube.exceptions import RegexMatchError

    from music_album_creation.downloading import CMDYoutubeDownloader
    youtube = CMDYoutubeDownloader()

    with pytest.raises(RegexMatchError):
        youtube.download_trials(
            INVALID_URL,
            str(tmp_path_factory.mktemp("unit-test")),
            times=1,
            delay=0.8,
        )
