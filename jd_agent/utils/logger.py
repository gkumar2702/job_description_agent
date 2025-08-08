"""
Logging configuration for JD Agent.
"""

import structlog
import sys
from typing import Any
import logging

# Configure stdlib logging (for tests that expect .name)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)

# Configure structlog for JSON output but bind stdlib logger
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    cache_logger_on_first_use=True,
)


class _CompatLogger:
    """Wrapper that provides a `.name` attribute for structlog logger compatibility."""

    def __init__(self, name: str | None):
        self._name = name or "jd_agent"
        self._logger = structlog.get_logger(self._name)

    @property
    def name(self) -> str:
        return self._name

    # Proxy common methods to structlog
    def bind(self, *args, **kwargs):
        self._logger = self._logger.bind(*args, **kwargs)
        return self

    def debug(self, *args, **kwargs):
        return self._logger.debug(*args, **kwargs)

    def info(self, *args, **kwargs):
        return self._logger.info(*args, **kwargs)

    def warning(self, *args, **kwargs):
        return self._logger.warning(*args, **kwargs)

    def error(self, *args, **kwargs):
        return self._logger.error(*args, **kwargs)

    def exception(self, *args, **kwargs):
        return self._logger.exception(*args, **kwargs)


def get_logger(name: str | None = None) -> Any:
    # Return a wrapper that exposes `.name` and proxies to structlog
    return _CompatLogger(name)