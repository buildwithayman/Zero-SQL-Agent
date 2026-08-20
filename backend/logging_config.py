"""
Structured Logging Configuration
Provides formatted, production-grade server logging with automatic credential masking.
"""

import logging
import re
import sys

# Sensitive patterns to redact from logs
SENSITIVE_PATTERNS = [
    (re.compile(r'(password["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE), r'\1***REDACTED***\3'),
    (re.compile(r'(bearer\s+)([A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_=]*)', re.IGNORECASE), r'\1***REDACTED_TOKEN***'),
    (re.compile(r'(gsk_[A-Za-z0-9]+)', re.IGNORECASE), r'***REDACTED_API_KEY***'),
    (re.compile(r'(postgresql:\/\/[^:]+:)([^@]+)(@)', re.IGNORECASE), r'\1***REDACTED_PASSWORD***\3'),
]


class SensitiveDataFilter(logging.Filter):
    """Log filter that scrubs credentials and tokens from all log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern, replacement in SENSITIVE_PATTERNS:
                msg = pattern.sub(replacement, msg)
            record.msg = msg
        return True


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configures root application logger with sensitive data scrubbing."""
    logger = logging.getLogger("zerosql")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Avoid adding duplicate handlers on re-init
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)

    return logger
