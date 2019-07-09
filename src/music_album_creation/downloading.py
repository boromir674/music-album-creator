#!/usr/bin/python3

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
    def download(cls, video_url, directory, spawn=True, verbose=True, supress_stdout=False):
        """
        Downloads a video from youtube given a url, converts it to mp3 and stores in input directory.\n
        :param str video_url:
        :param str directory:
        :param bool spawn:
        :param bool verbose:
        :param bool supress_stdout:
        :return:
        """
        args = cls._args[:-1] + ['{}/{}'.format(directory, cls._args[-1])] + [video_url]
        if verbose:
            print("Downloading stream '{}' and converting to mp3 ..".format(video_url))
        if spawn:
            _ = subprocess.Popen(args, stderr=subprocess.STDOUT, **cls._capture_stdout[supress_stdout])
        else:
            ro = subprocess.run(args, stderr=subprocess.PIPE, **cls._capture_stdout[supress_stdout])
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
        for subclass in (TokenParameterNotInVideoInfoError, InvalidUrlError, UnavailableVideoError):
            if re.search(subclass.reg, stderror):
                return subclass(video_url, stderror)
        return Exception(AbstractYoutubeDownloaderError(video_url, stderror)._msg)


#### EXCEPTIONS
import abc
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
    reg = '"token" parameter not in video info for unknown reason'
    def __init__(self, video_url, stderror):
        AbstractYoutubeDownloaderError.__init__(self, video_url, stderror)
        Exception.__init__(self, self._msg)

class InvalidUrlError(Exception, AbstractYoutubeDownloaderError):
    """Invalid url error"""
    reg = r'is not a valid URL\.'
    def __init__(self, video_url, stderror):
        AbstractYoutubeDownloaderError.__init__(self, video_url, stderror, msg="Invalid url '{}'.".format(video_url))
        Exception.__init__(self, self._short_msg)

class UnavailableVideoError(Exception, AbstractYoutubeDownloaderError):
    """Wrong url error"""
    reg = r'ERROR: This video is unavailable\.'
    def __init__(self, video_url, stderror):
        AbstractYoutubeDownloaderError.__init__(self, video_url, stderror, msg="Unavailable video at '{}'.".format(video_url))
        Exception.__init__(self, self._msg)
