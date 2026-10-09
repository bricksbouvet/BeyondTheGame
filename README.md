# Beyond The Game – Telegram bot

A small, privacy-conscious Telegram bot (Python + python-telegram-bot + SQLite) that sends football fans to a free
introductory video on <https://www.netmark.ai/super>.

> **Status honesty:** this code has been unit-tested locally, but **it has not been run against the real Telegram
> API, not deployed, and not submitted to or approved by Telegram Ads.** See *What is verified* below.

---

## 1. Architecture and key decisions

```
main.py                 wiring: handlers, error handler, command list, graceful shutdown
config.py               env-var loading + validation (token never printed)
logging_config.py       logging with token redaction; silences httpx URL logging
database.py             SQLite (WAL), parameterised queries, thread-safe
messages.py             ALL user-facing text (single place to edit/verify claims)
keyboards.py            inline keyboards (URL buttons for the video/website)
handlers/start.py       /start /video /website
handlers/menu.py        /menu /about /help /privacy /updates /stop /deletedata + menu callbacks
handlers/admin.py       /admin /stats /export /broadcast (admin IDs only)
services/analytics.py   campaign parsing, event tracking, summary, CSV export
services/broadcast.py   rate-limited consent-based sender (no Telegram imports → testable)
tests/                  34 tests (9 handler tests need python-telegram-bot installed)
```

Key decisions:

* **/start replies first, tracks second.** The welcome + button are sent before any database work, and analytics
  failures are caught so they can never block the user.
* **The CTA is a native inline URL button** with the exact URL `https://www.netmark.ai/super` – works on Telegram
  mobile, desktop and web, requires no registration, and only opens when the user taps it.
* **Telegram does not tell bots when a URL button is tapped.** So the bot measures what it *can*: starts, returning
  users, campaign source, commands such as `/video`, and About/Help button presses. It does **not** claim to know
  who opened or watched anything. Measure that on the website (section 6).
* **Opt-in, not opt-out, for promotional messages.** Users receive broadcasts only after sending `/updates`;
  `/stop` reverses it; users who block the bot are removed automatically.
* **Data minimisation.** Stored: numeric Telegram user ID, timestamps, start count, campaign code, opt-in flag,
  event names. Not stored: name, username, phone, email, location, message text. CSV export is aggregated (no user IDs).
  `/deletedata` erases a user's data.
* **Admin features exist only if `ADMIN_IDS` is set**, and every admin handler re-checks the ID. Broadcasts require
  a preview + confirmation, send at ≤30 msg/s (default 20), honour `RetryAfter`, and report sent/failed/blocked.
* **Plain-text messages only** (no Markdown/HTML parsing) so text can never break formatting or inject markup.

---

## 2. Pre-launch compliance flags (read before running ads)

I read the live page at <https://www.netmark.ai/super> on 2026-10-09. These items need *your* decision/verification.
I did not invent anything beyond what the page states, and I cannot guarantee Telegram Ads approval
(<https://ads.telegram.org/guidelines>).

1. **Affiliate nature.** The page says it is an *independent affiliate page, not operated or endorsed by SuperOne
   unless stated*. The brief's ad copy and welcome message don't say this, so I added a one-line disclosure to the
   welcome message and a fuller `/about`. Remove only if you're sure that's compliant (`messages.py`).
2. **Paid products / financial risk.** The page says SuperOne sells **paid packs with a commission structure** and
   mentions **token/crypto payouts carrying risk of total loss**. A reviewer may treat the destination as
   affiliate/financial/crypto-adjacent regardless of the "free video" framing. Check the ad rules for those categories.
3. **Video file name.** One embedded video file is named like "…2026-24000FansPassiveIncomeOpportunity.mp4". If the video
   itself makes income claims, it contradicts the page's "no income promised" statement and could breach the
   policy. **Watch both videos in full before launch.**
4. **Stale urgency banner.** The page shows "FOUNDER WINDOW CLOSES SEP 25 · 11:59 PM ET". Today is 2026-10-09, so that
   date has passed (or it's a recurring/fake countdown). Urgency that isn't real counts as deceptive; fix or remove it.
5. **Unfinished page.** It still contains placeholders: `[YOUR NAME / COMPANY, ADDRESS, CONTACT EMAIL]`,
   `[PRIVACY POLICY LINK]`, `[TERMS LINK]`, `© [YOUR NAME / BRAND]`. Reviewers and GDPR require these filled in.
6. **Ad copy.** "5 billion engaged with the last World Cup" and "Most only watched" are unsourced statistics, and
   "See how you can take part" doesn't say what that means (a trivia game with an optional affiliate program).
   Cite a source for the figure and make the ad consistent with the page.
7. **Project facts to confirm.** `/about` is limited to what the page says (game = SuperOne football trivia; video
   covers the game, football + AI, "your options"; optional 7-day email series; paid packs; risk statements). Confirm
   they're current. If you want more detail (rules, prizes, pricing), tell me the facts and I'll add them.
8. **Not affiliated with FIFA/clubs.** The bot says so; use no official logos in the profile picture.
9. **Operator contact.** Set `OPERATOR_CONTACT` so `/privacy` names who to contact.

---

## 3. Create the bot with BotFather

1. In Telegram open **@BotFather** → `/newbot`.
2. Display name: `Beyond The Game`. Username must end in `bot` – try `BeyondTheGameBot`; if taken, BotFather will say
   so; pick another (e.g. `BeyondTheGame_Bot`).
3. Copy the token BotFather returns (looks like `123456789:AAH…`). **Treat it like a password.** If it leaks: BotFather → `/revoke`.
4. Recommended text (accurate and consistent with the page):
   * `/setdescription` (≤512 chars): *Beyond The Game links to a free video overview of SuperOne, a football (soccer) trivia game. It is an independent affiliate promotion, not run by SuperOne, FIFA or any football body. No income is promised. Tap Start to see the free video button.*
   * `/setabouttext` (≤120 chars): *Free video overview of SuperOne football trivia. Independent affiliate promo. No income promised.*
   * `/setuserpic`: upload a simple dark-green/white/black football graphic that you own (no FIFA/club/team logos).
   * `/setcommands` is optional – the bot registers its command list itself at start-up.
5. Your numeric ID for `ADMIN_IDS`: message **@userinfobot**.

## 4. Configure

```bash
cp .env.example .env     # then edit .env
```
`BOT_TOKEN` (required), `ADMIN_IDS` (optional), `OPERATOR_CONTACT` (recommended). Other settings are documented in
`.env.example`. `.env` is git-ignored. The bot refuses to start with a missing/malformed token.

## 5. Run locally and test

```bash
python3 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest            # or: python -m unittest discover -s tests -t .
python main.py              # Ctrl+C stops it gracefully
```
Manual checklist (do this on a real phone **and** Telegram Desktop/Web):

- [ ] `/start` → welcome text appears immediately, big **▶ Watch the Free Video** button opens exactly `https://www.netmark.ai/super`
- [ ] Press Start twice, and with `https://t.me/<bot>?start=campaign_a` → no errors; `/stats` (admin) shows 1 user, campaign `campaign_a`
- [ ] `/video`, `/website`, `/menu`, `/about`, `/help`, `/privacy` all respond; every button works
- [ ] `/updates` then `/stop` toggles consent; `/deletedata` erases the record
- [ ] Non-admin account sending `/stats` gets only "I didn't understand that"
- [ ] Admin: `/broadcast test` with a second test account opted in → preview, confirm, report counts
- [ ] Stop and restart the bot → `/stats` numbers are unchanged

## 6. Measuring real website visits and video views

Telegram can't report URL-button taps, so use the website's own analytics (you control or can ask the page owner):

* Set `UTM_ENABLED=true` – buttons then open `…/super?utm_source=telegram&utm_medium=bot&utm_campaign=<campaign>`
  (this changes the URL from the bare one; keep `false` if you need the exact URL). Confirm the page keeps working with the parameters.
* Use a privacy-compliant tool (GA4, Plausible, Matomo) on the page to see sessions per `utm_campaign`, and add video
  play/progress events and form-submission events there. Honour consent rules (GDPR/ePrivacy) on the page.
* Use a **different** deep link per ad (`?start=campaign_a`, `?start=campaign_b`) – the bot logs the code it receives.
  Only `A–Z a–z 0–9 _ -`, up to 64 chars are accepted; anything else is ignored, never stored.

## 7. Deploy on a VPS (Ubuntu 22.04/24.04, beginner steps)

The bot uses long polling, so it needs **no domain, no open ports, no HTTPS** – only outbound internet.

```bash
# 1. as root on a fresh server: create an unprivileged user
adduser --disabled-password --gecos "" botuser
apt update && apt install -y python3 python3-venv python3-pip git
# 2. as botuser: upload the project (scp/git) to /home/botuser/beyond-the-game
su - botuser
cd beyond-the-game
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env && chmod 600 .env
.venv/bin/python main.py     # quick test; Ctrl+C when it works
exit
```
Create `/etc/systemd/system/beyondthegame.service` (as root):
```ini
[Unit]
Description=Beyond The Game Telegram bot
After=network-online.target
Wants=network-online.target

[Service]
User=botuser
WorkingDirectory=/home/botuser/beyond-the-game
ExecStart=/home/botuser/beyond-the-game/.venv/bin/python main.py
Restart=on-failure
RestartSec=5
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```
```bash
systemctl daemon-reload && systemctl enable --now beyondthegame
systemctl status beyondthegame           # should say "active (running)"
journalctl -u beyondthegame -f           # live logs
# update later: replace files, then
systemctl restart beyondthegame
```
**Backups:** copy `data/bot.sqlite3` regularly (e.g. `sqlite3 data/bot.sqlite3 ".backup /home/botuser/backup.db"`).
**Only run one instance per token**, otherwise Telegram returns a `Conflict` error.

## 8. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `Configuration error: BOT_TOKEN…` | `.env` missing/misnamed or token mistyped; no spaces/quotes around it |
| `InvalidToken` / `Unauthorized` | Token revoked or wrong – get a fresh one from BotFather |
| `Conflict: terminated by other getUpdates request` | Another copy of the bot is running with the same token (old terminal, another server) |
| Bot silent | `journalctl -u beyondthegame -n 100`; check server internet access; check you're messaging the right bot |
| `/stats` says "didn't understand" | Your ID isn't in `ADMIN_IDS`, or the bot wasn't restarted after editing `.env` |
| Button does nothing | URL must be `https://…`; check `WEBSITE_URL`; test on another client |
| `database is locked` | Two bot instances share the same DB file; run only one |
| Broadcast sends 0 | Nobody has sent `/updates` yet (opt-in is required by design) |
| Admin command menu missing | The admin must open the bot once; restart the bot afterwards |

## 9. What is implemented vs. what still needs you

**Implemented:** all 7 required commands plus `/menu`, `/updates`, `/deletedata`; four-option menu; exact-URL inline
button; deep-link campaign tracking; analytics (unique/returning/daily/weekly/campaign/events); admin stats, CSV
export, confirmed broadcasts to opted-in users with delivery/failure/blocked counts and rate limiting; SQLite
persistence; token-safe logging; graceful shutdown; 34 automated tests; deployment docs.

**Verified here:** config validation, analytics/database logic (dedup, windows, persistence, opt-in/out, deletion),
broadcast runner, token redaction, message content rules – plus the 9 handler tests, run against a **minimal fake
`telegram` module** (not the real library).

**NOT verified (you must do):** running with the real python-telegram-bot and the live Telegram API (`main.py` wiring,
broadcast callback flow, CSV upload, `set_my_commands`), behaviour on real mobile/desktop/web clients, deployment,
Telegram Ads approval. Pinned range `python-telegram-bot>=22.0,<23.0` was chosen from memory – confirm the installed
version with `pip show python-telegram-bot` and run the tests.

**Manual configuration:** BotFather setup, profile picture, `.env`, server, website-side analytics, fixing the page
issues in section 2.

Known limits: events table grows indefinitely (prune old rows if you reach very large volumes); single-process
SQLite is sized for thousands–hundreds of thousands of users, not millions; `/stats` shows one global dashboard in chat
only (no web dashboard, by design).
