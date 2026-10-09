"""All user-facing text (plain text only, no parse_mode, so nothing can break formatting).

Statements about the project come ONLY from the public page https://www.netmark.ai/super
as read on 2026-10-09. Re-verify before launch and whenever the page changes.
"""
from __future__ import annotations

BOT_NAME = "Beyond The Game"

# Exact welcome text requested in the brief.
WELCOME_BASE = (
    "⚽ Welcome to Beyond The Game!\n\n"
    "Millions of football fans follow the world's biggest tournaments. "
    "But watching is only one way to engage with the game.\n\n"
    "Curious to discover another way to get involved?\n\n"
    "🎬 Watch the free introductory video to learn more."
)
# Added for transparency (the linked page is an independent affiliate page). Edit with care.
DISCLOSURE_LINE = "ℹ️ Independent affiliate promotion. No income is promised. Tap About for details."
WELCOME = f"{WELCOME_BASE}\n\n{DISCLOSURE_LINE}"

BTN_VIDEO = "▶ Watch the Free Video"
BTN_ABOUT = "ℹ️ About the Project"
BTN_WEBSITE = "🌐 Official Website"
BTN_HELP = "❓ Help"

VIDEO = (
    "🎬 Free introductory video\n\n"
    "A short overview of the SuperOne football (soccer) trivia game: how it plays, "
    "football and AI, and your options.\n\n"
    "The button opens the official page in your browser. "
    "This bot never asks for your email, phone number or payment."
)

WEBSITE = "🌐 Official website\n\nTap the button to open the page that hosts the free video."

ABOUT = (
    "ℹ️ About the project\n\n"
    "This bot points to a free video overview of SuperOne, a football (soccer) trivia game.\n\n"
    "According to the page, the video covers:\n"
    "• The game – how the trivia works and how players take part\n"
    "• Football + AI – why the two are an interesting combination\n"
    "• Your options – just playing, or the optional affiliate program\n\n"
    "Please know before you click:\n"
    "• The page is run by an independent affiliate of SuperOne and is not an official "
    "SuperOne website. This bot is part of that affiliate promotion.\n"
    "• The page offers an optional free 7-day email series. Signing up is done on the "
    "website, never in this bot.\n"
    "• SuperOne also offers paid packs with a commission structure. The terms are set by "
    "the company - read them in full before buying anything.\n"
    "• The page states that no income is promised, that most participants in affiliate "
    "programs earn little or nothing, and that token/crypto payouts carry risk, "
    "including loss of the full amount.\n\n"
    "This bot is not affiliated with FIFA, any football association, club or tournament."
)

HELP = (
    "❓ How to use Beyond The Game\n\n"
    "/start – Welcome and the free-video button\n"
    "/video – About the free video\n"
    "/about – About the project\n"
    "/website – Link to the official website\n"
    "/menu – Show the menu\n"
    "/privacy – What data is stored\n"
    "/updates – Opt in to optional project updates\n"
    "/stop – Opt out of promotional messages\n"
    "/deletedata – Delete the data stored about you\n\n"
    "You will only receive promotional messages if you choose /updates."
)

MENU = "📋 Menu"

PRIVACY_TEMPLATE = (
    "🔒 Privacy notice\n\n"
    "Stored by this bot:\n"
    "• Your numeric Telegram user ID (needed to reply to you)\n"
    "• When you first and last used the bot, and how many times you pressed Start\n"
    "• The campaign code in the link you used to open the bot, if any\n"
    "• Simple interaction events (for example: you used /video)\n"
    "• Whether you opted in to project updates\n\n"
    "Not collected: your name or username, phone number, email address, location, or "
    "message contents.\n\n"
    "Telegram cannot tell the bot whether you tap the website button, so the bot does "
    "not know if you opened or watched anything.\n\n"
    "The website is operated separately and has its own privacy policy and forms.\n\n"
    "Your choices: /stop (no promotional messages), /deletedata (erase everything stored "
    "about you).\n\n"
    "Contact: {contact}"
)

UPDATES_ON = (
    "✅ You will receive occasional optional project updates from this bot.\n"
    "Send /stop at any time to unsubscribe."
)
STOP_DONE = (
    "✅ You will not receive promotional messages from this bot. "
    "You can still use all commands. Send /updates if you change your mind."
)
DELETED = "🗑 Your data has been deleted. If you use the bot again, a new record will be created."
UNKNOWN = "I didn't understand that. Use /start for the free video, or /help for all commands."
ERROR = "⚠️ Something went wrong on our side. Please try again in a moment."

BROADCAST_FOOTER = "\n\n— Beyond The Game · Send /stop to unsubscribe from these messages."


def privacy_text(contact: str) -> str:
    return PRIVACY_TEMPLATE.format(contact=contact or "(not configured by the operator)")
