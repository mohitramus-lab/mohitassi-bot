from telegram import Update
from telegram.ext import ContextTypes
from database import get_conn
from utils import is_team_member


async def add_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    if not context.args:
        await update.message.reply_text(
            "Usage: `/addcontact <name> | <@username_or_id> | <label>`\n"
            "Example: `/addcontact Ali Khan | @ali_khan | client`\n"
            "Labels: client, supplier, team, partner, other",
            parse_mode="Markdown"
        )
        return

    full = " ".join(context.args)
    parts = [p.strip() for p in full.split("|")]
    name     = parts[0] if len(parts) > 0 else "Unknown"
    username = parts[1] if len(parts) > 1 else ""
    label    = parts[2] if len(parts) > 2 else "general"

    # Extract Telegram ID if numeric
    tg_id = None
    uname = username
    if username.lstrip("@").isdigit():
        tg_id = int(username.lstrip("@"))
        uname = None
    elif username.startswith("@"):
        uname = username[1:]

    conn = get_conn()
    conn.execute(
        "INSERT INTO contacts (name, telegram_id, username, label, added_by) VALUES (?,?,?,?,?)",
        (name, tg_id, uname, label, update.effective_user.id)
    )
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"✅ Contact added!\n👤 *{name}*\n🏷 Label: `{label}`\n📱 {username}",
        parse_mode="Markdown"
    )


async def delete_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: `/delcontact <id>`", parse_mode="Markdown")
        return
    conn = get_conn()
    conn.execute("DELETE FROM contacts WHERE id=?", (context.args[0],))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Contact `{context.args[0]}` deleted.", parse_mode="Markdown")


async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: `/contact <name or username>`", parse_mode="Markdown")
        return
    query = "%" + " ".join(context.args) + "%"
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM contacts WHERE name LIKE ? OR username LIKE ?", (query, query)
    ).fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("No contact found.")
        return
    text = "🔍 *Search Results:*\n━━━━━━━━━━━━━\n"
    for r in rows:
        text += f"*[{r['id']}]* 👤 *{r['name']}*\n"
        if r['username']: text += f"   📱 @{r['username']}\n"
        if r['telegram_id']: text += f"   🆔 `{r['telegram_id']}`\n"
        if r['phone']: text += f"   📞 {r['phone']}\n"
        text += f"   🏷 {r['label']}\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def list_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    label_filter = context.args[0] if context.args else None
    conn = get_conn()
    if label_filter:
        rows = conn.execute("SELECT * FROM contacts WHERE label=? ORDER BY name", (label_filter,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM contacts ORDER BY label, name").fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("No contacts yet. Use `/addcontact` to add.", parse_mode="Markdown")
        return

    text = f"👥 *Contacts* {f'({label_filter})' if label_filter else ''}:\n━━━━━━━━━━━━━\n"
    current_label = None
    for r in rows:
        if r['label'] != current_label:
            current_label = r['label']
            text += f"\n🏷 *{current_label.upper()}*\n"
        text += f"  [{r['id']}] *{r['name']}*"
        if r['username']: text += f" @{r['username']}"
        text += "\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    if not context.args or "|" not in " ".join(context.args):
        await update.message.reply_text(
            "Usage: `/broadcast <label> | <message>`\n"
            "Example: `/broadcast client | We have a new offer for you!`",
            parse_mode="Markdown"
        )
        return

    full = " ".join(context.args)
    label, _, message = full.partition("|")
    label   = label.strip()
    message = message.strip()

    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM contacts WHERE label=? AND telegram_id IS NOT NULL", (label,)
    ).fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text(f"❌ No contacts with label `{label}` and known Telegram ID.", parse_mode="Markdown")
        return

    sent = 0
    failed = 0
    for r in rows:
        try:
            await context.bot.send_message(chat_id=r['telegram_id'], text=message)
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"📢 *Broadcast Complete*\n✅ Sent: `{sent}` | ❌ Failed: `{failed}`",
        parse_mode="Markdown"
    )
