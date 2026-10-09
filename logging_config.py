"""Logging setup that never leaks the bot token."""
from __future__ import annotations

import logging


class RedactTokenFilter(logging.Filter):
    def __init__(self, secret: str) -> None:
        super().__init__()
        self._secret = secret

    def filter(self, record: logging.LogRecord) -> bool:
        if self._secret:
            try:
                message = record.getMessage()
            except Exception:  # malformed log call; don't crash logging
                return True
            if self._secret in message:
                record.msg = message.replace(self._secret, "[REDACTED]")
                record.args = None
        return True


def setup_logging(level: str, secret: str = "") -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    flt = RedactTokenFilter(secret)
    for handler in logging.getLogger().handlers:
        handler.addFilter(flt)
    # httpx logs full request URLs, which contain the bot token, at INFO level.
    for noisy in ("httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
