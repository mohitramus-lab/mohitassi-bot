from telegram import Update
from telegram.ext import ContextTypes
from database import get_conn
from utils import is_team_member
from datetime import datetime
import pytz
from config import TIMEZONE


def get_tz():
    try:
        return pytz.timezone(TIMEZONE)
    except Exception:
        return pytz.utc


async def schedule_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    if not context.args:
        await update.message.reply_text(
            "Usage: `/schedule <chat_id> | <YYYY-MM-DD HH:MM> | <message> | <repeat>`\n\n"
            "Repeat options: `none`, `daily`, `weekly`\n\n"
            "Example:\n"
            "`/schedule 123456789 | 2024-12-25 09:00 | Merry Christmas! | none`\n\n"
            "💡 To get a chat ID, forward a message from that chat to @userinfobot",
            parse_mode="Markdown"
        )
        return

    full = " ".join(context.args)
    parts = [p.strip() for p in full.split("|")]

    if len(parts) < 3:
        await update.message.reply_text("❌ Need at least: `chat_id | time | message`", parse_mode="Markdown")
        return

    try:
        chat_id = int(parts[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid chat_id. Must be a number.", parse_mode="Markdown")
        return

    send_at = parts[1]
    message = parts[2]
    repeat  = parts[3] if len(parts) > 3 else "none"

    # Validate datetime
    try:
        tz = get_tz()
        dt = tz.localize(datetime.strptime(send_at, "%Y-%m-%d %H:%M"))
    except ValueError:
        await update.message.reply_text("❌ Invalid time format. Use: `YYYY-MM-DD HH:MM`", parse_mode="Markdown")
        return

    conn = get_conn()
    conn.execute(
        "INSERT INTO schedules (chat_id, message, send_at, repeat, created_by) VALUES (?,?,?,?,?)",
        (chat_id, message, send_at, repeat, update.effective_user.id)
    )
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"⏰ *Message Scheduled!*\n"
        f"📍 Chat ID: `{chat_id}`\n"
        f"🕐 Time: `{send_at}` ({TIMEZONE})\n"
        f"🔁 Repeat: `{repeat}`\n"
        f"💬 Message: {message[:50]}{'...' if len(message) > 50 else ''}",
        parse_mode="Markdown"
    )


async def list_schedules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    conn = get_conn()
    rows = conn.execute("SELECT * FROM schedules WHERE status='pending' ORDER BY send_at").fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("No pending scheduled messages.")
        return
    text = "⏰ *Scheduled Messages:*\n━━━━━━━━━━━━━\n"
    for r in rows:
        text += (
            f"*[{r['id']}]* 🕐 `{r['send_at']}` → Chat `{r['chat_id']}`\n"
            f"   🔁 {r['repeat']} | 💬 {r['message'][:40]}...\n\n"
        )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cancel_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: `/cancelschedule <id>`", parse_mode="Markdown")
        return
    conn = get_conn()
    conn.execute("UPDATE schedules SET status='cancelled' WHERE id=?", (context.args[0],))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Schedule `{context.args[0]}` cancelled.", parse_mode="Markdown")


async def check_schedules(context: ContextTypes.DEFAULT_TYPE):
    """Called every 60 seconds by the job queue"""
    tz  = get_tz()
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")

    conn = get_conn()
    due = conn.execute(
        "SELECT * FROM schedules WHERE status='pending' AND send_at <= ?", (now,)
    ).fetchall()

    for s in due:
        try:
            await context.bot.send_message(chat_id=s['chat_id'], text=s['message'])
            if s['repeat'] == "none":
                conn.execute("UPDATE schedules SET status='sent' WHERE id=?", (s['id'],))
            elif s['repeat'] == "daily":
                from datetime import timedelta
                dt = datetime.strptime(s['send_at'], "%Y-%m-%d %H:%M") + timedelta(days=1)
                conn.execute("UPDATE schedules SET send_at=? WHERE id=?", (dt.strftime("%Y-%m-%d %H:%M"), s['id']))
            elif s['repeat'] == "weekly":
                from datetime import timedelta
                dt = datetime.strptime(s['send_at'], "%Y-%m-%d %H:%M") + timedelta(weeks=1)
                conn.execute("UPDATE schedules SET send_at=? WHERE id=?", (dt.strftime("%Y-%m-%d %H:%M"), s['id']))
        except Exception as e:
            conn.execute("UPDATE schedules SET status='failed' WHERE id=?", (s['id'],))

    conn.commit()
    conn.close()
