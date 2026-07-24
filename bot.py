import logging
import asyncio
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)
from config import BOT_TOKEN
import payment, autoreply, contacts, scheduler, organizer, admin, content

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ── ADMIN / GENERAL ──────────────────────────────────────────
    app.add_handler(CommandHandler("start",       admin.start))
    app.add_handler(CommandHandler("help",        admin.help_cmd))
    app.add_handler(CommandHandler("addteam",     admin.add_team_member))
    app.add_handler(CommandHandler("removeteam",  admin.remove_team_member))
    app.add_handler(CommandHandler("team",        admin.list_team))
    app.add_handler(CommandHandler("stats",       admin.stats))

    # ── PAYMENT ──────────────────────────────────────────────────
    app.add_handler(CommandHandler("token",       payment.register_token))
    app.add_handler(CommandHandler("confirm",     payment.confirm_payment))
    app.add_handler(CommandHandler("reject",      payment.reject_payment))
    app.add_handler(CommandHandler("payments",    payment.list_payments))
    app.add_handler(MessageHandler(filters.PHOTO, payment.handle_photo))

    # ── AUTO-REPLY ────────────────────────────────────────────────
    app.add_handler(CommandHandler("addreply",    autoreply.add_reply))
    app.add_handler(CommandHandler("delreply",    autoreply.delete_reply))
    app.add_handler(CommandHandler("listreplies", autoreply.list_replies))
    app.add_handler(CommandHandler("autoreplyon", autoreply.enable_autoreply))
    app.add_handler(CommandHandler("autoreplyoff",autoreply.disable_autoreply))

    # ── CONTACTS ──────────────────────────────────────────────────
    app.add_handler(CommandHandler("addcontact",  contacts.add_contact))
    app.add_handler(CommandHandler("delcontact",  contacts.delete_contact))
    app.add_handler(CommandHandler("contact",     contacts.get_contact))
    app.add_handler(CommandHandler("contacts",    contacts.list_contacts))
    app.add_handler(CommandHandler("broadcast",   contacts.broadcast_message))

    # ── SCHEDULER ─────────────────────────────────────────────────
    app.add_handler(CommandHandler("schedule",    scheduler.schedule_message))
    app.add_handler(CommandHandler("schedules",   scheduler.list_schedules))
    app.add_handler(CommandHandler("cancelschedule", scheduler.cancel_schedule))

    # ── ORGANIZER ─────────────────────────────────────────────────
    app.add_handler(CommandHandler("tag",         organizer.tag_chat))
    app.add_handler(CommandHandler("untag",       organizer.untag_chat))
    app.add_handler(CommandHandler("chats",       organizer.list_tagged_chats))
    app.add_handler(CommandHandler("note",        organizer.add_note))
    app.add_handler(CommandHandler("notes",       organizer.list_notes))
    app.add_handler(CommandHandler("delnote",     organizer.delete_note))
    app.add_handler(CommandHandler("pin",         organizer.pin_important))

    # ── CONTENT AGENT (viral finance ideas) ──────────────────────
    app.add_handler(CommandHandler("ideas",       content.daily_ideas))
    app.add_handler(CommandHandler("idea",        content.content_idea))
    app.add_handler(CommandHandler("hook",        content.viral_hook))
    app.add_handler(CommandHandler("calendar",    content.content_calendar))
    app.add_handler(CommandHandler("contenthelp", content.content_help))

    # ── INLINE BUTTONS ────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(payment.handle_callback, pattern="^pay_"))
    app.add_handler(CallbackQueryHandler(organizer.handle_callback, pattern="^org_"))

    # ── CATCH-ALL (auto-reply engine) ─────────────────────────────
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        autoreply.handle_message
    ))

    # ── SCHEDULER JOB ─────────────────────────────────────────────
    app.job_queue.run_repeating(scheduler.check_schedules, interval=60, first=10)

    # ── DAILY CONTENT AGENT JOB ───────────────────────────────────
    app.job_queue.run_daily(content.send_daily_ideas, time=content.daily_time())

    logger.info("✅ Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
