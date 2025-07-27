"""
Logging configuration for JD Agent.
"""

import structlog  # type: ignore
import sys
from typing import Any

# Configure structlog for JSON output
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    cache_logger_on_first_use=True,
)

def get_logger(name: str | None = None) -> Any:
    return structlog.get_logger(name) 