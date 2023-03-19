import json
import logging
import re
from abc import ABC
from pathlib import Path
from time import sleep
from typing import Union

from pytube import YouTube

logger = logging.getLogger(__name__)



class CMDYoutubeDownloader:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(CMDYoutubeDownloader, cls).__new__(cls)
        return cls.__instance

    def download(self, video_url: str, directory: Union[str, Path], **kwargs):
        self._download(video_url, directory)

    @classmethod
    def _download(cls, video_url, directory):
        # output dir where to store the stream
        output_dir = Path(directory)

        yt = YouTube(video_url)
        
        # get avaialbe streams
        streams = yt.streams

        # filter streams by audio only
        audio_streams = streams.filter(only_audio=True)

        # find highest quality audio stream
        # we currently judge quality by bitrate (higher is better)
        best_audio_stream = audio_streams.order_by('bitrate')[-1]

        # highest_quality_audio_stream = audio_streams.order_by('abr').desc().first()

        # find highest quality audio stream
        # find audio only stream with highest reported kbps (as quality measure)
        # best_audio_stream = yt.streams.filter(only_audio=True).order_by('bitrate')[-1]

        # Download the audio stream
        local_file = best_audio_stream.download(
            output_path=str(output_dir),
            filename=f'{yt.title}.mp4',  # since this is an audio-only stream, the file will be mp4
            filename_prefix=None,
            skip_existing=True,  # Skip existing files, defaults to True
            timeout=None,  # Request timeout length in seconds. Uses system default
            max_retries=3  # Number of retries to attempt after socket timeout. Defaults to 0
        )
        logger.error("Downloaded from Youtube: %s", json.dumps({
            'title': yt.title,
            'local_file' : str(local_file),
        }, indent=4, sort_keys=True))
        return local_file

    def download_trials(self, video_url, directory, times=10, delay=1, **kwargs):
        i = 0
        while i < times - 1:
            try:
                return self._download(video_url, directory)
            except TooManyRequestsError as e:
                logger.info(e)
                i += 1
                sleep(delay)
        return self._download(video_url, directory)


class YoutubeDownloaderErrorFactory(object):
    @staticmethod
    def create_with_message(msg):
        return Exception(msg)

    @staticmethod
    def create_from_stderr(stderror, video_url):
        exception_classes = (
            UploaderIDExtractionError,
            TokenParameterNotInVideoInfoError, InvalidUrlError, UnavailableVideoError, TooManyRequestsError, CertificateVerificationError, HTTPForbiddenError)
        for subclass in exception_classes:
            if subclass.reg.search(stderror):
                return subclass(video_url, stderror)
        s = "NOTE: None of the predesinged exceptions' regexs [{}] matched. Perhaps you want to derive a new subclass from AbstractYoutubeDownloaderError to account for this youtube-dl exception with string to parse <S>{}</S>'".format(', '.join(['"{}"'.format(_.reg) for _ in exception_classes]), stderror)
        return Exception(AbstractYoutubeDownloaderError(video_url, stderror)._msg + '\n' + s)


#### EXCEPTIONS

class AbstractYoutubeDownloaderError(ABC):

    def __init__(self, *args, **kwargs):
        super(AbstractYoutubeDownloaderError, self).__init__()
        if len(args) > 1:
            self.video_url = args[0]
            self.stderr = args[1]
        elif len(args) > 0:
            self.video_url = args[0]
        self._msg = "YoutubeDownloader generic error."
        self._short_msg = kwargs.get('msg')
        if args or 'msg' in kwargs:
            self._msg = '\n'.join([_ for _ in [kwargs.get('msg', ''), getattr(self, 'stderr', '')] if _])


class TokenParameterNotInVideoInfoError(Exception, AbstractYoutubeDownloaderError):
    """Token error"""
    reg = re.compile('"token" parameter not in video info for unknown reason')

    def __init__(self, video_url, stderror):
        AbstractYoutubeDownloaderError.__init__(self, video_url, stderror)
        Exception.__init__(self, self._msg)

class InvalidUrlError(Exception, AbstractYoutubeDownloaderError):
    """Invalid url error"""
    reg = re.compile(r'is not a valid URL\.')

    def __init__(self, video_url, stderror):
        AbstractYoutubeDownloaderError.__init__(self, video_url, stderror, msg="Invalid url '{}'.".format(video_url))
        Exception.__init__(self, self._short_msg)

class UnavailableVideoError(Exception, AbstractYoutubeDownloaderError):
    """Wrong url error"""
    reg = re.compile(r'ERROR: Video unavailable')

    def __init__(self, video_url, stderror):
        AbstractYoutubeDownloaderError.__init__(self, video_url, stderror, msg="Unavailable video at '{}'.".format(video_url))
        Exception.__init__(self, self._msg)

class TooManyRequestsError(Exception, AbstractYoutubeDownloaderError):
    """Too many requests (for youtube) to serve"""
    reg = re.compile(r"(?:ERROR: Unable to download webpage: HTTP Error 429: Too Many Requests|WARNING: unable to download video info webpage: HTTP Error 429)")

    def __init__(self, video_url, stderror):
        AbstractYoutubeDownloaderError.__init__(self, video_url, stderror, msg="Too many requests for youtube at the moment.".format(video_url))
        Exception.__init__(self, self._msg)

class CertificateVerificationError(Exception, AbstractYoutubeDownloaderError):
    """This can happen when downloading is requested from a server like scrutinizer.io\n
    ERROR: Unable to download webpage: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get
    local issuer certificate (_ssl.c:1056)> (caused by URLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED]
    certificate verify failed: unable to get local issuer certificate (_ssl.c:1056)')))
    """
    reg = re.compile(r"ERROR: Unable to download webpage: <urlopen error \[SSL: CERTIFICATE_VERIFY_FAILED\]")

    def __init__(self, video_url, stderror):
        AbstractYoutubeDownloaderError.__init__(self, video_url, stderror,
                                                msg="Unable to download webpage because ssl certificate verification failed:\n[SSL: CERTIFICATE_VERIFY_FAILED] certificate "
                                                    "verify failed: unable to get local issuer certificate (_ssl.c:1056)> (caused by "
                                                    "URLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: "
                                                    "unable to get local issuer certificate (_ssl.c:1056)')))")
        Exception.__init__(self, self._msg)


class HTTPForbiddenError(Exception, AbstractYoutubeDownloaderError):
    reg = re.compile(r"ERROR: unable to download video data: HTTP Error 403: Forbidden")

    def __init__(self, video_url, stderror):
        AbstractYoutubeDownloaderError.__init__(self, video_url, stderror, msg="HTTP 403 Forbidden for some reason.".format(video_url))
        Exception.__init__(self, self._msg)


class UploaderIDExtractionError(Exception, AbstractYoutubeDownloaderError):
    reg = re.compile(r"ERROR: Unable to extract uploader id")

    def __init__(self, video_url, stderror):
        AbstractYoutubeDownloaderError.__init__(self, video_url, stderror, msg="Maybe update the youtube-dl binary/executable.".format(video_url))
        Exception.__init__(self, self._msg)
