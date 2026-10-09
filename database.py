"""SQLite storage. Stores only: numeric Telegram user ID, timestamps, counters,
campaign codes, opt-in flag and anonymous interaction events."""
from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY,
  first_seen TEXT NOT NULL,
  last_seen TEXT NOT NULL,
  start_count INTEGER NOT NULL DEFAULT 0,
  first_campaign TEXT,
  last_campaign TEXT,
  promo_opt_in INTEGER NOT NULL DEFAULT 0,
  blocked INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  user_id INTEGER NOT NULL,
  event_type TEXT NOT NULL,
  campaign TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_type_ts ON events(event_type, ts);
CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id);
CREATE TABLE IF NOT EXISTS broadcasts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  admin_id INTEGER NOT NULL,
  recipients INTEGER NOT NULL,
  sent INTEGER NOT NULL DEFAULT 0,
  failed INTEGER NOT NULL DEFAULT 0,
  blocked INTEGER NOT NULL DEFAULT 0,
  finished INTEGER NOT NULL DEFAULT 0
);
"""

_TS_FORMAT = "%Y-%m-%dT%H:%M:%S"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime(_TS_FORMAT)


class Database:
    """Thin, thread-safe wrapper. All queries are parameterised."""

    def __init__(self, path: str) -> None:
        if path != ":memory:":
            Path(path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        with self._lock:
            if path != ":memory:":
                self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # ---- users -------------------------------------------------------
    def touch_user(
        self,
        user_id: int,
        campaign: Optional[str] = None,
        is_start: bool = False,
        now: Optional[datetime] = None,
    ) -> bool:
        """Create/update a user. Returns True only if this is the user's first /start."""
        ts = iso(now or utcnow())
        campaign = campaign if is_start else None
        with self._lock, self._conn:
            row = self._conn.execute(
                "SELECT start_count FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            if row is None:
                self._conn.execute(
                    "INSERT INTO users (user_id, first_seen, last_seen, start_count,"
                    " first_campaign, last_campaign) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, ts, ts, 1 if is_start else 0, campaign, campaign),
                )
                return is_start
            self._conn.execute(
                "UPDATE users SET last_seen = ?, blocked = 0,"
                " start_count = start_count + ?,"
                " first_campaign = COALESCE(first_campaign, ?),"
                " last_campaign = COALESCE(?, last_campaign)"
                " WHERE user_id = ?",
                (ts, 1 if is_start else 0, campaign, campaign, user_id),
            )
            return is_start and row["start_count"] == 0

    def get_user_campaign(self, user_id: int) -> Optional[str]:
        with self._lock:
            row = self._conn.execute(
                "SELECT last_campaign FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
        return row["last_campaign"] if row else None

    def set_promo_opt_in(self, user_id: int, value: bool) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "UPDATE users SET promo_opt_in = ? WHERE user_id = ?", (1 if value else 0, user_id)
            )

    def is_promo_opted_in(self, user_id: int) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT promo_opt_in FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
        return bool(row and row["promo_opt_in"])

    def promo_recipients(self) -> List[int]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT user_id FROM users WHERE promo_opt_in = 1 AND blocked = 0 ORDER BY user_id"
            ).fetchall()
        return [r["user_id"] for r in rows]

    def mark_blocked(self, user_id: int) -> None:
        """User blocked the bot: stop messaging them."""
        with self._lock, self._conn:
            self._conn.execute(
                "UPDATE users SET blocked = 1, promo_opt_in = 0 WHERE user_id = ?", (user_id,)
            )

    def delete_user(self, user_id: int) -> None:
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM events WHERE user_id = ?", (user_id,))
            self._conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

    # ---- events ------------------------------------------------------
    def record_event(
        self,
        user_id: int,
        event_type: str,
        campaign: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO events (ts, user_id, event_type, campaign) VALUES (?, ?, ?, ?)",
                (iso(now or utcnow()), user_id, event_type, campaign),
            )

    # ---- statistics --------------------------------------------------
    def stats(self, now: Optional[datetime] = None) -> Dict:
        now = now or utcnow()
        today_start = iso(now.replace(hour=0, minute=0, second=0, microsecond=0))
        week_start = iso(now - timedelta(days=7))
        with self._lock:
            q = self._conn.execute
            total_users = q("SELECT COUNT(*) FROM users WHERE start_count >= 1").fetchone()[0]
            returning = q("SELECT COUNT(*) FROM users WHERE start_count > 1").fetchone()[0]
            starts_today = q(
                "SELECT COUNT(*) FROM events WHERE event_type='start' AND ts >= ?", (today_start,)
            ).fetchone()[0]
            starts_7d = q(
                "SELECT COUNT(*) FROM events WHERE event_type='start' AND ts >= ?", (week_start,)
            ).fetchone()[0]
            unique_7d = q(
                "SELECT COUNT(DISTINCT user_id) FROM events WHERE event_type='start' AND ts >= ?",
                (week_start,),
            ).fetchone()[0]
            opted_in = q(
                "SELECT COUNT(*) FROM users WHERE promo_opt_in = 1 AND blocked = 0"
            ).fetchone()[0]
            by_type = {
                r[0]: r[1]
                for r in q("SELECT event_type, COUNT(*) FROM events GROUP BY event_type")
            }
            campaigns = [
                (r[0], r[1], r[2])
                for r in q(
                    "SELECT COALESCE(campaign, '(none)'), COUNT(*), COUNT(DISTINCT user_id)"
                    " FROM events WHERE event_type='start' GROUP BY 1 ORDER BY 2 DESC LIMIT 10"
                )
            ]
            broadcasts = [
                dict(r)
                for r in q(
                    "SELECT id, ts, recipients, sent, failed, blocked, finished"
                    " FROM broadcasts ORDER BY id DESC LIMIT 5"
                )
            ]
        return {
            "total_users": total_users,
            "returning_users": returning,
            "starts_today": starts_today,
            "starts_7d": starts_7d,
            "unique_starters_7d": unique_7d,
            "opted_in": opted_in,
            "events_by_type": by_type,
            "campaigns": campaigns,
            "broadcasts": broadcasts,
        }

    def export_rows(self) -> List[Tuple[str, str, str, int, int]]:
        """Aggregated rows (no user IDs): date, event_type, campaign, events, unique_users."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT substr(ts, 1, 10), event_type, COALESCE(campaign, '(none)'),"
                " COUNT(*), COUNT(DISTINCT user_id) FROM events"
                " GROUP BY 1, 2, 3 ORDER BY 1, 2, 3"
            ).fetchall()
        return [tuple(r) for r in rows]

    # ---- broadcasts --------------------------------------------------
    def create_broadcast(self, admin_id: int, recipients: int) -> int:
        with self._lock, self._conn:
            cur = self._conn.execute(
                "INSERT INTO broadcasts (ts, admin_id, recipients) VALUES (?, ?, ?)",
                (iso(utcnow()), admin_id, recipients),
            )
            return int(cur.lastrowid)

    def finish_broadcast(self, broadcast_id: int, sent: int, failed: int, blocked: int) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "UPDATE broadcasts SET sent=?, failed=?, blocked=?, finished=1 WHERE id=?",
                (sent, failed, blocked, broadcast_id),
            )
