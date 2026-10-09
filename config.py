"""Configuration loading and validation (environment variables only)."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Mapping, Optional

DEFAULT_WEBSITE_URL = "https://www.netmark.ai/super"
_TOKEN_RE = re.compile(r"^\d{5,}:[A-Za-z0-9_-]{20,}$")
_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class ConfigError(ValueError):
    """Raised when configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    bot_token: str = field(repr=False)  # never printed
    admin_ids: frozenset = frozenset()
    database_path: str = "data/bot.sqlite3"
    log_level: str = "INFO"
    website_url: str = DEFAULT_WEBSITE_URL
    utm_enabled: bool = False
    broadcast_rate_per_second: float = 20.0
    operator_contact: str = ""


def parse_admin_ids(raw: Optional[str]) -> frozenset:
    ids = set()
    for part in (raw or "").split(","):
        part = part.strip()
        if not part:
            continue
        if not re.fullmatch(r"\d{1,15}", part):
            raise ConfigError("ADMIN_IDS must be comma-separated numeric Telegram user IDs.")
        ids.add(int(part))
    return frozenset(ids)


def _parse_bool(raw: Optional[str], default: bool = False) -> bool:
    if raw is None or raw.strip() == "":
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"Invalid boolean value: {raw!r}")


def load_settings(env: Optional[Mapping[str, str]] = None) -> Settings:
    """Build Settings from `env` (defaults to os.environ, after loading .env if present)."""
    if env is None:
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:  # python-dotenv is optional at runtime
            pass
        env = os.environ

    token = (env.get("BOT_TOKEN") or "").strip()
    if not token:
        raise ConfigError("BOT_TOKEN is not set. Copy .env.example to .env and add your token.")
    if not _TOKEN_RE.match(token):
        raise ConfigError("BOT_TOKEN does not look like a valid Telegram bot token.")

    website_url = (env.get("WEBSITE_URL") or DEFAULT_WEBSITE_URL).strip()
    if not website_url.startswith("https://"):
        raise ConfigError("WEBSITE_URL must start with https://")

    log_level = (env.get("LOG_LEVEL") or "INFO").strip().upper()
    if log_level not in _VALID_LOG_LEVELS:
        raise ConfigError(f"LOG_LEVEL must be one of {sorted(_VALID_LOG_LEVELS)}")

    raw_rate = (env.get("BROADCAST_RATE_PER_SECOND") or "20").strip()
    try:
        rate = float(raw_rate)
    except ValueError as exc:
        raise ConfigError("BROADCAST_RATE_PER_SECOND must be a number.") from exc
    if not 0 < rate <= 30:
        raise ConfigError("BROADCAST_RATE_PER_SECOND must be > 0 and <= 30.")

    return Settings(
        bot_token=token,
        admin_ids=parse_admin_ids(env.get("ADMIN_IDS")),
        database_path=(env.get("DATABASE_PATH") or "data/bot.sqlite3").strip(),
        log_level=log_level,
        website_url=website_url,
        utm_enabled=_parse_bool(env.get("UTM_ENABLED")),
        broadcast_rate_per_second=rate,
        operator_contact=(env.get("OPERATOR_CONTACT") or "").strip()[:200],
    )


def build_destination_url(base_url: str, campaign: Optional[str], utm_enabled: bool) -> str:
    """Return the exact base URL, or (only if UTM is enabled) the URL with UTM tags."""
    if not utm_enabled:
        return base_url
    from urllib.parse import urlencode

    params = {"utm_source": "telegram", "utm_medium": "bot"}
    if campaign:
        params["utm_campaign"] = campaign
    sep = "&" if "?" in base_url else "?"
    return f"{base_url}{sep}{urlencode(params)}"
