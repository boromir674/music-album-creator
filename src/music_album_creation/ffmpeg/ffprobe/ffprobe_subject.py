"""FFProbe Subject that runs ffprobe in python subprocess."""
from software_patterns import Singleton

from ..run_cli import execute_command_in_subprocess

__all__ = ['FFProbeSubject']


# Our implementation of the Subject class (see the Proxy pattern)
class FFProbeSubject(metaclass=Singleton):
    """The standard FFProbe Subject class proxies the ffprobe CLI."""

    def __init__(self, ffprobe_binary: str):
        self.ffprobe_binary = ffprobe_binary

    def __call__(self, *args, **kwargs):
        return execute_command_in_subprocess(self.ffprobe_binary, *args, **kwargs)
