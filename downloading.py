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
            print('Downloading...')
        if spawn:
            child = subprocess.Popen(args, stderr=subprocess.STDOUT, universal_newlines=True)
            stdout_string = child.communicate()[0]
            if debug:
                print(stdout_string)
            rc = child.returncode
        else:
            rc = subprocess.run(args, stderr=subprocess.STDOUT, **self._debug_flag_hash[debug]).returncode
        return rc
        # if rc == 0 or rc == '0':
        #     self.suceeded = True
        # else:
        #     self.suceeded = False

    @classmethod
    def cmd(cls, video_url):
        return cls._cmd.format(url=video_url)

youtube = YoutubeDownloader()


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: downloading.py VIDEO_URL')
        sys.exit(1)

    url = sys.argv[1]
    # url = 'https://www.youtube.com/watch?v=V5YOhcAof8I'
    youtube.download(url, '/tmp/', spawn=True, verbose=False, debug=True)
