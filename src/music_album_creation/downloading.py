import logging
import os
import re
import json
from pathlib import Path
import subprocess
from typing import Optional
import sys
from abc import ABCMeta, abstractmethod
from time import sleep
from pytube import YouTube
from music_album_creation.ffmpeg import FFMPEG


logger = logging.getLogger(__name__)


ffmpeg = FFMPEG(
    os.environ.get('MUSIC_FFMPEG', 'ffmpeg')
)


class AbstractYoutubeDownloader(object):
    __metaclass__ = ABCMeta
    @abstractmethod
    def download(self, video_url, directory, **kwargs):
        raise NotImplementedError


class AbstractYoutubeDL(AbstractYoutubeDownloader):
    update_command_args = ('sudo', 'python' '-m', 'pip', 'install', '--upgrade', 'youtube-dl')
    update_backend_command = ' '.join(update_command_args)

    already_up_to_date_reg = re.compile(r'python\d[\d.]*/(site-packages \(\d[\d.]*\))',)
    updated_reg = re.compile(r'Collecting [\w\-_]+==(\d[\d.]*)')

    def download(self, video_url, directory, **kwargs):
        raise NotImplementedError

    # @classmethod
    # def update_backend(cls):
    #     args = ['python', '-m', 'pip', 'install', '--user', '--upgrade', 'youtube-dl']
    #     output = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #     stdout = str(output.stdout, encoding='utf-8')
    #     if output.returncode == 0:
    #         match = cls.requirement_dir_reg.search(stdout)
    #         if match:
    #             logger.info("Backend 'youtube-dl' already up-to-date in '{}'".format(match.group(1)))
    #         else:
    #             logger.info("Updated with command '{}' to version {}".format(' '.join(args), cls.updated_reg.search(stdout)))
    #     else:
    #         logging.error("Something not documented happened while attempting to update youtube_dl: {}".format(str(output.stderr, encoding='utf-8')))


class CMDYoutubeDownloader(AbstractYoutubeDL):
    _args = ['youtube-dl', '--extract-audio', '--audio-quality', '0', '--audio-format', 'mp3', '-o', '%(title)s.%(ext)s']
    __instance = None
    youtube_dl_executable: Optional[str] = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(CMDYoutubeDownloader, cls).__new__(cls)
        return cls.__instance

    def download(self, video_url, directory, suppress_certificate_validation=False, **kwargs):
        self._download(video_url, directory, suppress_certificate_validation=suppress_certificate_validation)

    @classmethod
    def _download(cls, video_url, directory, **kwargs):
        # output dir where to store the stream
        output_dir = Path(directory)

        # https://www.youtube.com/watch?v=FVLHDm8xZBo
        # args = [
        #     os.environ.get('YOUTUBE_DL', 'youtube-dl'),
        #     '--extract-audio',
        #     '--audio-quality',
        #     '0',
        #     '--audio-format',
        #     'mp3',
        #     '-o',
        #     '{}/{}'.format(directory, template), video_url
        # ]
        # # If suppress HTTPS certificate validation
        # if kwargs.get('suppress_certificate_validation', False):
        #     args.insert(1, '--no-check-certificate')
        # logger.info("Executing '{}'".format(' '.join(args)))

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
            max_retries=0  # Number of retries to attempt after socket timeout. Defaults to 0
        )
        logger.error("Downloaded from Youtube: %s", json.dumps({
            'title': yt.title,
            'local_file' : str(local_file),
        }, indent=4, sort_keys=True))

        # LEGACY CODE
        # process = subprocess.Popen(args, stderr=subprocess.PIPE)  # stdout gets streamed in terminal
        # stdout, stderr = process.communicate()
        # if process.returncode != 0:
        #     if 2 < sys.version_info[0]:
        #         stderr = str(stderr, encoding='utf-8')
        #     else:
        #         stderr = str(stderr)
        #     raise YoutubeDownloaderErrorFactory.create_from_stderr(stderr, video_url)

        # manually convert webm to mp3 (ffmpeg)
        # TODO delegate this to a separate module
        """
        Audio options:
        -aframes number     set the number of audio frames to output
        -aq quality         set audio quality (codec-specific)
        -ar rate            set audio sampling rate (in Hz)
        -ac channels        set number of audio channels
        -an                 disable audio
        -acodec codec       force audio codec ('copy' to copy stream)
        -vol volume         change audio volume (256=normal)
        -af filter_graph    set audio filters
        """
        print('-- HERE --')
        # result = ffmpeg(
        #     '-y',  # force file overwrite if exists
        #     '-i',
        #     str(local_file),
        #     '-vn',  # disable video (keep only audio even though we expect to receive only audio)
        #     '-acodec',
        #     # we do not use the full ffmpeg pipeline (encode -> decode frames -> ecnode data packets ...)
        #     'copy',   # we make sure we discarded the video stream and copy the audio stream as is
        #     str(Path(f'{output_dir}/{yt.title}.mp4'))
        # )
        # print(result.stdout)
        # if result.exit_code != 0:
        #     logger.error("Ffmpeg exit code: %s", result.exit_code)
        #     logger.error("Ffmpeg stdout: %s", result.stdout)
        #     logger.error("Ffmpeg error: %s", result.stderr)
        #     raise Exception(result.stderr)
        #     # raise YoutubeDownloaderErrorFactory.create_from_stderr(result.stderr, video_url)

        return local_file

    def download_trials(self, video_url, directory, times=10, delay=1, **kwargs):
        i = 0
        while i < times - 1:
            try:
                return self._download(video_url, directory, **kwargs)
            except TooManyRequestsError as e:
                logger.info(e)
                i += 1
                sleep(delay)
        return self._download(video_url, directory, **kwargs)


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

class AbstractYoutubeDownloaderError(object):
    __metaclass__ = ABCMeta

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
