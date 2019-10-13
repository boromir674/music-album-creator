import logging
import re
import subprocess
from abc import ABCMeta, abstractmethod
from time import sleep

logger = logging.getLogger(__name__)

# # Create handlers
# c_handler = logging.StreamHandler()
# f_handler = logging.FileHandler('file.log')
# c_handler.setLevel(logging.INFO)
# f_handler.setLevel(logging.DEBUG)
#
# # Create formatters and add it to handlers
# c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# c_handler.setFormatter(c_format)
# f_handler.setFormatter(f_format)
#
# # Add handlers to the logger
# logger.addHandler(c_handler)
# logger.addHandler(f_handler)



class AbstractYoutubeDownloader(metaclass=ABCMeta):

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

    @classmethod
    def update_backend(cls):
        args = ['python', '-m', 'pip', 'install', '--user', '--upgrade', 'youtube-dl']
        output = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = str(output.stdout, encoding='utf-8')
        if output.returncode == 0:
            match = cls.requirement_dir_reg.search(stdout)
            if match:
                logger.info("Backend 'youtube-dl' already up-to-date in '{}'".format(match.group(1)))
            else:
                logger.info("Updated with command '{}' to version {}".format(' '.join(args), cls.updated_reg.search(stdout)))
        else:
            logging.error("Something not documented happened while attempting to update youtube_dl: {}".format(str(output.stderr, encoding='utf-8')))


class CMDYoutubeDownloader(AbstractYoutubeDL):
    _args = ['youtube-dl', '--extract-audio', '--audio-quality', '0', '--audio-format', 'mp3', '-o', '%(title)s.%(ext)s']
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def download(self, video_url, directory, suppress_certificate_validation=False, **kwargs):
        self._download(video_url, directory, suppress_certificate_validation=suppress_certificate_validation)

    @classmethod
    def _download(cls, video_url, directory, **kwargs):
        template = kwargs.get('template', '%(title)s.%(ext)s')
        args = ['youtube-dl', '--extract-audio', '--audio-quality', '0', '--audio-format', 'mp3', '-o', '{}/{}'.format(directory, template), video_url]
        # If suppress HTTPS certificate validation
        if kwargs.get('suppress_certificate_validation', False):
            args.insert(1, '--no-check-certificate')
        logger.info("Executing '{}'".format(' '.join(args)))
        ro = subprocess.run(args, stderr=subprocess.PIPE)  # stdout gets streamed in terminal
        if ro.returncode != 0:
            stderr = str(ro.stderr, encoding='utf-8')
            raise YoutubeDownloaderErrorFactory.create_from_stderr(stderr, video_url)

    def download_trials(self, video_url, directory, times=10, delay=1, **kwargs):
        i = 0
        while i < times - 1:
            try:
                self.download(video_url, directory, **kwargs)
                return
            except TooManyRequestsError as e:
                logger.info(e)
                i += 1
                sleep(delay)
        self.download(video_url, directory, **kwargs)


class YoutubeDownloaderErrorFactory:
    @staticmethod
    def create_with_message(msg):
        return Exception(msg)

    @staticmethod
    def create_from_stderr(stderror, video_url):
        exception_classes = (TokenParameterNotInVideoInfoError, InvalidUrlError, UnavailableVideoError, TooManyRequestsError, CertificateVerificationError)
        for subclass in exception_classes:
            if subclass.reg.search(stderror):
                return subclass(video_url, stderror)
        s = "NOTE: None of the predesinged exceptions' regexs [{}] matched. Perhaps you want to derive a new subclass from AbstractYoutubeDownloaderError to account for this youtube-dl exception with string to parse <S>{}</S>'".format(', '.join(['"{}"'.format(_.reg) for _ in exception_classes]), stderror)
        return Exception(AbstractYoutubeDownloaderError(video_url, stderror)._msg + '\n' + s)


#### EXCEPTIONS

class AbstractYoutubeDownloaderError(metaclass=ABCMeta):
    def __init__(self, *args, **kwargs):
        super().__init__()
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
    reg = re.compile(r'ERROR: This video is unavailable\.')

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
