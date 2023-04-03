import json
import logging
from typing import Any, Protocol

from software_patterns import Proxy

__all__ = ['FFProbeProxy']


logger = logging.getLogger(__name__)


class CLIResult(Protocol):
    exit_code: int
    stdout: str
    stderr: str


class FFMpegSubjectType(Protocol):
    def __init__(self, ffmpeg_binary: str):
        ...

    def __call__(self, *ffmpeg_cli_args, **subprocess_settings) -> CLIResult:
        ...


class FFMPEGProxy(Proxy[FFMpegSubjectType]):
    """Proxy class for the ffmpeg CLI."""

    def __call__(self, *ffmpeg_cli_args: str, **subprocess_settings: Any) -> CLIResult:
        logger.error(
            "Running ffmpeg: %s", json.dumps(list(ffmpeg_cli_args), indent=4, sort_keys=True)
        )
        res = self._proxy_subject(*ffmpeg_cli_args, **subprocess_settings)
        # logger.info("FFMPEG:\n%s", res.stderr)
        return res
