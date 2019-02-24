#!/usr/bin/python3

import re
import subprocess


class YoutubeDownloader:
    wrong_url_message = 'ERROR: This video is unavailable.'
    _cmd = 'youtube-dl --extract-audio --audio-quality 0 --audio-format mp3 -o "%(title)s.%(ext)s" "{url}"'
    _args = ['youtube-dl', '--extract-audio', '--audio-quality', '0', '--audio-format', 'mp3', '-o', '%(title)s.%(ext)s']
    _capture_stdout = {True: {'stdout': subprocess.PIPE},  # captures std out ie: print(str(ro.stdout, encoding='utf-8'))
                       False: {}}  # does not capture stdout and it streams it in the terminal}

    def download(self, video_url, directory, spawn=True, verbose=True, supress_stdout=False):
        """
        Downloads a video from youtube given a url, converts it to mp3 and stores in input directory.\n
        :param str video_url:
        :param str directory:
        :param bool spawn:
        :param bool verbose:
        :param bool supress_stdout:
        :return:
        """
        args = self._args[:-1] + ['{}/{}'.format(directory, self._args[-1])] + [video_url]
        if verbose:
            print("Downloading stream '{}' and converting to mp3 ..".format(video_url))
        if spawn:
            _ = subprocess.Popen(args, stderr=subprocess.STDOUT, **self._capture_stdout[supress_stdout])
        else:
            ro = subprocess.run(args, stderr=subprocess.PIPE, **self._capture_stdout[supress_stdout])
            if ro.returncode != 0:
                stderr = str(ro.stderr, encoding='utf-8')
                print('STDERR:', stderr)
                if re.search(self.wrong_url_message, stderr):
                    raise WrongYoutubeUrl("The '{}' youtube url doesn't exist.".format(video_url))
                raise DownloadError("Failed to download url '{}'".format(video_url))

    @classmethod
    def cmd(cls, video_url):
        return cls._cmd.format(url=video_url)


class DownloadError(Exception):
    def __init__(self, msg): super().__init__(msg)
class WrongYoutubeUrl(Exception):
    def __init__(self, msg): super().__init__(msg)


youtube = YoutubeDownloader()




if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: downloading.py VIDEO_URL')
        sys.exit(1)

    url = sys.argv[1]
    # url = 'https://www.youtube.com/watch?v=V5YOhcAof8I'
    try:
        youtube.download(url, '/tmp/', spawn=False, verbose=True, supress_stdout=False)
    except WrongYoutubeUrl as e:
        print(e)
    except DownloadError as e:
        print(e)
        print("Something else went wrong with the youtube-dl cl program")