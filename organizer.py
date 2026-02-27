from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database import get_conn
from utils import is_team_member


async def tag_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    if not context.args or "|" not in " ".join(context.args):
        await update.message.reply_text(
            "Usage: `/tag <chat_id> | <tag>`\n"
            "Example: `/tag -1001234567890 | VIP Client`\n\n"
            "💡 Use `/tag here | <tag>` to tag the current chat",
            parse_mode="Markdown"
        )
        return

    full = " ".join(context.args)
    chat_str, _, tag = full.partition("|")
    chat_str = chat_str.strip()
    tag      = tag.strip()

    if chat_str.lower() == "here":
        chat_id   = update.effective_chat.id
        chat_name = update.effective_chat.title or update.effective_chat.full_name or str(chat_id)
    else:
        try:
            chat_id = int(chat_str)
        except ValueError:
            await update.message.reply_text("❌ Invalid chat_id.", parse_mode="Markdown")
            return
        chat_name = chat_str

    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO chat_tags (chat_id, chat_name, tag, added_by) VALUES (?,?,?,?)",
        (chat_id, chat_name, tag, update.effective_user.id)
    )
    conn.commit()
    conn.close()
    await update.message.reply_text(f"🏷 Chat `{chat_id}` tagged as *{tag}*", parse_mode="Markdown")


async def untag_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: `/untag <chat_id> <tag>`", parse_mode="Markdown")
        return
    chat_id = context.args[0]
    tag     = " ".join(context.args[1:])
    conn = get_conn()
    conn.execute("DELETE FROM chat_tags WHERE chat_id=? AND tag=?", (chat_id, tag))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Tag *{tag}* removed from chat `{chat_id}`", parse_mode="Markdown")


async def list_tagged_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    tag_filter = " ".join(context.args) if context.args else None
    conn = get_conn()
    if tag_filter:
        rows = conn.execute("SELECT * FROM chat_tags WHERE tag LIKE ? ORDER BY tag", (f"%{tag_filter}%",)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM chat_tags ORDER BY tag, chat_name").fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("No tagged chats yet. Use `/tag` to organise your chats.", parse_mode="Markdown")
        return

    text = "🗂 *Tagged Chats:*\n━━━━━━━━━━━━━\n"
    current_tag = None
    for r in rows:
        if r['tag'] != current_tag:
            current_tag = r['tag']
            text += f"\n🏷 *{current_tag}*\n"
        text += f"  • `{r['chat_id']}` — {r['chat_name']}\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def add_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    if not context.args or "|" not in " ".join(context.args):
        await update.message.reply_text(
            "Usage: `/note <title> | <content>`\n"
            "Example: `/note Ali Payment | PKR 50,000 received on 25 Dec`",
            parse_mode="Markdown"
        )
        return

    full = " ".join(context.args)
    title, _, content = full.partition("|")
    title   = title.strip()
    content = content.strip()

    conn = get_conn()
    conn.execute(
        "INSERT INTO notes (chat_id, title, content, added_by) VALUES (?,?,?,?)",
        (update.effective_chat.id, title, content, update.effective_user.id)
    )
    conn.commit()
    conn.close()
    await update.message.reply_text(f"📝 Note saved!\n*{title}*\n{content}", parse_mode="Markdown")


async def list_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    search = "%" + " ".join(context.args) + "%" if context.args else "%"
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM notes WHERE title LIKE ? OR content LIKE ? ORDER BY created_at DESC LIMIT 20",
        (search, search)
    ).fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("No notes found. Use `/note` to save one.", parse_mode="Markdown")
        return

    text = "📝 *Notes:*\n━━━━━━━━━━━━━\n"
    for r in rows:
        text += f"*[{r['id']}]* 📌 *{r['title']}*\n{r['content']}\n🕐 {r['created_at'][:16]}\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def delete_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: `/delnote <id>`", parse_mode="Markdown")
        return
    conn = get_conn()
    conn.execute("DELETE FROM notes WHERE id=?", (context.args[0],))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Note `{context.args[0]}` deleted.", parse_mode="Markdown")


async def pin_important(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    if not context.args or "|" not in " ".join(context.args):
        await update.message.reply_text(
            "Usage: `/pin <title> | <info>`\n"
            "Saves important info as a pinned note with 📌 tag.",
            parse_mode="Markdown"
        )
        return

    full = " ".join(context.args)
    title, _, content = full.partition("|")
    conn = get_conn()
    conn.execute(
        "INSERT INTO notes (chat_id, title, content, added_by) VALUES (?,?,?,?)",
        (update.effective_chat.id, f"📌 {title.strip()}", content.strip(), update.effective_user.id)
    )
    conn.commit()
    conn.close()
    await update.message.reply_text(f"📌 Pinned: *{title.strip()}*", parse_mode="Markdown")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
