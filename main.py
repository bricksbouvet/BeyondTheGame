"""Beyond The Game – Telegram bot entry point."""
from __future__ import annotations

import logging

from telegram import BotCommand, BotCommandScopeChat, Update
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import keyboards as kb
import messages as m
from config import ConfigError, Settings, load_settings
from database import Database
from handlers import admin, menu, start
from handlers.common import SERVICES_KEY, Services
from logging_config import setup_logging
from services.analytics import AnalyticsService

logger = logging.getLogger(__name__)

PUBLIC_COMMANDS = [
    BotCommand("start", "Welcome and free video"),
    BotCommand("video", "About the free video"),
    BotCommand("about", "About the project"),
    BotCommand("website", "Official website"),
    BotCommand("menu", "Show menu"),
    BotCommand("help", "How to use this bot"),
    BotCommand("privacy", "Privacy notice"),
    BotCommand("updates", "Opt in to project updates"),
    BotCommand("stop", "Stop promotional messages"),
    BotCommand("deletedata", "Delete my data"),
]
ADMIN_COMMANDS = PUBLIC_COMMANDS + [
    BotCommand("admin", "Admin help"),
    BotCommand("stats", "Statistics"),
    BotCommand("export", "Export CSV"),
    BotCommand("broadcast", "Message opted-in users"),
]


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled exception", exc_info=context.error)  # token is redacted by log filter
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(m.ERROR)
        except TelegramError:
            pass


async def post_init(app: Application) -> None:
    await app.bot.set_my_commands(PUBLIC_COMMANDS)
    for admin_id in app.bot_data[SERVICES_KEY].settings.admin_ids:
        try:
            await app.bot.set_my_commands(ADMIN_COMMANDS, scope=BotCommandScopeChat(admin_id))
        except TelegramError:
            logger.info("Could not set admin command list (admin hasn't started the bot yet)")
    logger.info("Bot is ready.")


async def post_shutdown(app: Application) -> None:
    app.bot_data[SERVICES_KEY].db.close()
    logger.info("Shut down cleanly.")


def build_application(settings: Settings, db: Database) -> Application:
    app = ApplicationBuilder().token(settings.bot_token).post_init(post_init).post_shutdown(post_shutdown).build()
    app.bot_data[SERVICES_KEY] = Services(settings=settings, db=db, analytics=AnalyticsService(db))

    private = filters.ChatType.PRIVATE
    for name, fn in [
        ("start", start.start_command),
        ("video", start.video_command),
        ("website", start.website_command),
        ("menu", menu.menu_command),
        ("about", menu.about_command),
        ("help", menu.help_command),
        ("privacy", menu.privacy_command),
        ("updates", menu.updates_command),
        ("stop", menu.stop_command),
        ("deletedata", menu.deletedata_command),
    ]:
        app.add_handler(CommandHandler(name, fn, filters=private))
    app.add_handler(CallbackQueryHandler(menu.menu_callback, pattern=r"^menu:(about|help)$"))

    if settings.admin_ids:  # admin interface only exists when explicitly configured
        for name, fn in [
            ("admin", admin.admin_command),
            ("stats", admin.stats_command),
            ("export", admin.export_command),
            ("broadcast", admin.broadcast_command),
        ]:
            app.add_handler(CommandHandler(name, fn, filters=private))
        app.add_handler(CallbackQueryHandler(admin.broadcast_callback, pattern=r"^bc:(confirm|cancel)$"))

    app.add_handler(MessageHandler(private & (filters.COMMAND | filters.TEXT), menu.fallback))
    app.add_error_handler(on_error)
    return app


def main() -> None:
    try:
        settings = load_settings()
    except ConfigError as exc:
        raise SystemExit(f"Configuration error: {exc}")
    setup_logging(settings.log_level, settings.bot_token)
    if not settings.operator_contact:
        logger.warning("OPERATOR_CONTACT is not set; /privacy will say contact is not configured.")
    if not settings.admin_ids:
        logger.info("ADMIN_IDS empty: admin interface disabled.")
    db = Database(settings.database_path)
    app = build_application(settings, db)
    # run_polling installs SIGINT/SIGTERM handlers and shuts down gracefully.
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
