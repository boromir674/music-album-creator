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


class FFProbeSubjectType(Protocol):
    def __init__(self, ffprobe_binary: str):
        ...

    def __call__(self, *ffprobe_cli_args, **subprocess_settings) -> CLIResult:
        ...


class FFProbeProxy(Proxy[FFProbeSubjectType]):
    """Proxy class for the ffprobe CLI."""

    def __call__(self, *ffprobe_cli_args: str, **subprocess_settings: Any) -> CLIResult:
        logger.info(
            "Running ffmpeg: %s", json.dumps(list(ffprobe_cli_args), indent=4, sort_keys=True)
        )
        return self._proxy_subject(*ffprobe_cli_args, **subprocess_settings)
