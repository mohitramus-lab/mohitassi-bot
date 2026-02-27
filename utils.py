from telegram import Update
from database import get_conn
from config import OWNER_ID
import functools


async def is_team_member(update: Update) -> bool:
    user_id = update.effective_user.id
    if user_id == OWNER_ID:
        return True
    conn = get_conn()
    row = conn.execute("SELECT 1 FROM team WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    if row:
        return True
    await update.message.reply_text("❌ You are not authorised to use this bot.")
    return False


def owner_only(func):
    @functools.wraps(func)
    async def wrapper(update: Update, context, *args, **kwargs):
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("❌ This command is for the bot owner only.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def fmt_dt(dt_str: str) -> str:
    if not dt_str:
        return "N/A"
    return dt_str[:16]
