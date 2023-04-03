"""FFMpeg Subject that runs ffmpeg in python subprocess."""
from software_patterns import Singleton

from ..run_cli import execute_command_in_subprocess

__all__ = ['FFMpegSubject']


# Our implementation of the Subject class (see the Proxy pattern)
class FFMPEGSubject(metaclass=Singleton):
    """The standard FFMPEGSubject class proxies the ffmpeg CLI."""

    def __init__(self, ffmpeg_binary: str):
        self.ffmpeg_binary = ffmpeg_binary

    def __call__(self, *args, **kwargs):
        return execute_command_in_subprocess(self.ffmpeg_binary, *args, **kwargs)
