#!/usr/bin/python3

import abc
import re
import subprocess


class YoutubeDownloader:

    _cmd = 'youtube-dl --extract-audio --audio-quality 0 --audio-format mp3 -o "%(title)s.%(ext)s" "{url}"'
    _args = ['youtube-dl', '--extract-audio', '--audio-quality', '0', '--audio-format', 'mp3', '-o', '%(title)s.%(ext)s']
    _capture_stdout = {True: {'stdout': subprocess.PIPE},  # captures std out ie: print(str(ro.stdout, encoding='utf-8'))
                       False: {}}  # does not capture stdout and it streams it in the terminal}

    update_command_args = ('sudo', 'pip3', 'install', '--upgrade', 'youtube-dl')
    update_backend_command = ' '.join(update_command_args)

    @classmethod
    def download(cls, video_url, directory, spawn=True, verbose=True, supress_stdout=False, suppress_certificate_validation=False):
        """
        Downloads a video from youtube given a url, converts it to mp3 and stores in input directory.\n
        :param str video_url:
        :param str directory:
        :param bool spawn:
        :param bool verbose:
        :param bool supress_stdout:
        :param bool suppress_certificate_validation:
        :return:
        """
        cls.__download(video_url, directory, spawn=spawn, verbose=verbose, supress_stdout=supress_stdout, suppress_certificate_validation=suppress_certificate_validation)

    @classmethod
    def __download(cls, video_url, directory, **kwargs):
        args = cls._args[:-1] + ['{}/{}'.format(directory, cls._args[-1])] + [video_url]
        # If suppress HTTPS certificate validation
        if kwargs.get('suppress_certificate_validation', False):
            args.insert(1, '--no-check-certificate')
        if kwargs.get('verbose', False):
            print("Downloading stream '{}' and converting to mp3 ..".format(video_url))
        if kwargs.get('spawn', True):
            _ = subprocess.Popen(args, stderr=subprocess.STDOUT, **cls._capture_stdout[kwargs.get('supress_stdout', True)])
        else:
            ro = subprocess.run(args, stderr=subprocess.PIPE, **cls._capture_stdout[kwargs.get('supress_stdout', True)])
            if ro.returncode != 0:
                stderr = str(ro.stderr, encoding='utf-8')
                raise YoutubeDownloaderErrorFactory.create_from_stderr(stderr, video_url)

    @classmethod
    def update_backend(cls):
        ro = subprocess.run(cls.update_command_args, stderr=subprocess.PIPE, **cls._capture_stdout[False])
        return ro

    @classmethod
    def cmd(cls, video_url):
        return cls._cmd.format(url=video_url)


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

class AbstractYoutubeDownloaderError(metaclass=abc.ABCMeta):
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
