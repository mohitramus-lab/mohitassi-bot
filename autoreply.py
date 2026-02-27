from telegram import Update
from telegram.ext import ContextTypes
from database import get_conn
from utils import is_team_member


async def add_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    if not context.args:
        await update.message.reply_text(
            "Usage: `/addreply <keyword> | <reply text>`\n"
            "Example: `/addreply hello | Hi there! How can I help you?`\n\n"
            "Match types (add at end): `| exact` or `| startswith`\n"
            "Default is `contains` (matches if keyword is anywhere in message)",
            parse_mode="Markdown"
        )
        return

    full = " ".join(context.args)
    if "|" not in full:
        await update.message.reply_text("❌ Please separate keyword and reply with `|`", parse_mode="Markdown")
        return

    parts = full.split("|", 2)
    keyword    = parts[0].strip().lower()
    reply_text = parts[1].strip()
    match_type = parts[2].strip() if len(parts) > 2 else "contains"

    conn = get_conn()
    conn.execute(
        "INSERT INTO auto_replies (keyword, reply, match_type, created_by) VALUES (?,?,?,?)",
        (keyword, reply_text, match_type, update.effective_user.id)
    )
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"✅ Auto-reply added!\n🔑 Keyword: `{keyword}`\n💬 Reply: {reply_text}\n🔍 Match: `{match_type}`",
        parse_mode="Markdown"
    )


async def delete_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: `/delreply <id>`\nGet IDs with /listreplies", parse_mode="Markdown")
        return
    rid = context.args[0]
    conn = get_conn()
    conn.execute("DELETE FROM auto_replies WHERE id=?", (rid,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Auto-reply ID `{rid}` deleted.", parse_mode="Markdown")


async def list_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    conn = get_conn()
    rows = conn.execute("SELECT * FROM auto_replies ORDER BY id").fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("No auto-replies set up yet.\nUse `/addreply` to add one.", parse_mode="Markdown")
        return
    text = "🤖 *Auto-Replies:*\n━━━━━━━━━━━━━\n"
    for r in rows:
        text += f"*[{r['id']}]* 🔑 `{r['keyword']}` ({r['match_type']})\n    💬 {r['reply']}\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def enable_autoreply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    conn = get_conn()
    conn.execute("UPDATE autoreply_status SET enabled=1 WHERE id=1")
    conn.commit()
    conn.close()
    await update.message.reply_text("✅ Auto-reply is now *ON*", parse_mode="Markdown")


async def disable_autoreply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    conn = get_conn()
    conn.execute("UPDATE autoreply_status SET enabled=0 WHERE id=1")
    conn.commit()
    conn.close()
    await update.message.reply_text("🔴 Auto-reply is now *OFF*", parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Catch-all handler that checks every incoming message against auto-reply rules"""
    # Don't auto-reply to team members
    from config import TEAM_IDS
    if update.effective_user.id in TEAM_IDS:
        return

    conn = get_conn()
    status = conn.execute("SELECT enabled FROM autoreply_status WHERE id=1").fetchone()
    if not status or not status['enabled']:
        conn.close()
        return

    msg = update.message.text.lower().strip()
    rules = conn.execute("SELECT * FROM auto_replies ORDER BY id").fetchall()
    conn.close()

    for rule in rules:
        kw = rule['keyword']
        mt = rule['match_type']
        matched = False
        if mt == "exact"      and msg == kw:       matched = True
        elif mt == "startswith" and msg.startswith(kw): matched = True
        elif mt == "contains"   and kw in msg:      matched = True

        if matched:
            await update.message.reply_text(rule['reply'])
            return
