import subprocess


class YoutubeDownloader:
    """Downloads youtube videos in the same directory as this script/module belongs to"""
    _cmd = 'youtube-dl --extract-audio --audio-quality 0 --audio-format mp3 -o "%(title)s.%(ext)s" "{url}"'
    _args = ['youtube-dl', '--extract-audio', '--audio-quality', '0', '--audio-format', 'mp3', '-o', '%(title)s.%(ext)s']
    _debug_flag_hash = {True: {},
                        False: {'stdout': subprocess.PIPE}}

    def download(self, video_url, directory, spawn=True, verbose=True, debug=False):
        args = self._args[:-1] + ['{}/{}'.format(directory, self._args[-1])] + [video_url]
        self.suceeded = None
        if verbose:
            print("Downloading '{}' ..".format(video_url))
        if spawn:
            child = subprocess.Popen(args, stderr=subprocess.STDOUT, **self._debug_flag_hash[debug])
        else:
            # rc = subprocess.run(args, stderr=subprocess.STDOUT, **self._debug_flag_hash[debug]).returncode
            rc = subprocess.run(args, stderr=subprocess.PIPE, **self._debug_flag_hash[debug]).returncode
            if rc != 0:
                raise DownloadError("Failed to download url '{}'. Perhaps url doesn't exist.".format(video_url))

    @classmethod
    def cmd(cls, video_url):
        return cls._cmd.format(url=video_url)

class DownloadError(Exception):
    def __init__(self, msg):
        super().__init__(msg)

youtube = YoutubeDownloader()


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: downloading.py VIDEO_URL')
        sys.exit(1)

    url = sys.argv[1]
    # url = 'https://www.youtube.com/watch?v=V5YOhcAof8I'
    youtube.download(url, '/tmp/', spawn=True, verbose=False, debug=True)
