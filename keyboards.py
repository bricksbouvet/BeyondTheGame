"""Inline keyboards. The video/website buttons are URL buttons (work on mobile, desktop, web)."""
from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import messages as m

CB_ABOUT = "menu:about"
CB_HELP = "menu:help"
CB_BC_CONFIRM = "bc:confirm"
CB_BC_CANCEL = "bc:cancel"


def video_button(url: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(m.BTN_VIDEO, url=url)


def primary_keyboard(url: str) -> InlineKeyboardMarkup:
    """/start keyboard: one prominent full-width CTA, then two small helper buttons."""
    return InlineKeyboardMarkup(
        [
            [video_button(url)],
            [
                InlineKeyboardButton(m.BTN_ABOUT, callback_data=CB_ABOUT),
                InlineKeyboardButton(m.BTN_HELP, callback_data=CB_HELP),
            ],
        ]
    )


def video_only_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[video_button(url)]])


def website_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(m.BTN_WEBSITE, url=url)]])


def menu_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [video_button(url)],
            [
                InlineKeyboardButton(m.BTN_ABOUT, callback_data=CB_ABOUT),
                InlineKeyboardButton(m.BTN_WEBSITE, url=url),
            ],
            [InlineKeyboardButton(m.BTN_HELP, callback_data=CB_HELP)],
        ]
    )


def broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Send now", callback_data=CB_BC_CONFIRM),
                InlineKeyboardButton("✖ Cancel", callback_data=CB_BC_CANCEL),
            ]
        ]
    )
