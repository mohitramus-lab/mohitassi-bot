from telegram import Update
from telegram.ext import ContextTypes
from database import get_conn
from config import OWNER_ID, TEAM_IDS
from utils import is_team_member, owner_only, fmt_dt


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO team (user_id, username, name, added_by) VALUES (?,?,?,?)",
        (OWNER_ID, "owner", "Owner", OWNER_ID)
    )
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"👋 Hello *{user.first_name}*!\n\n"
        "🤖 *Your All-in-One Telegram Manager Bot*\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "💰 *PAYMENTS*\n"
        "  `/token <ref>` – Register payment token\n"
        "  `/confirm <ref>` – Confirm payment\n"
        "  `/reject <ref>` – Reject payment\n"
        "  `/payments` – View all payments\n\n"
        "🤖 *AUTO-REPLY*\n"
        "  `/addreply <keyword> | <reply>` – Add auto-reply\n"
        "  `/listreplies` – List all auto-replies\n"
        "  `/autoreplyon` / `/autoreplyoff` – Toggle\n\n"
        "👥 *CONTACTS*\n"
        "  `/addcontact <name> | @username | label`\n"
        "  `/contacts` – List contacts\n"
        "  `/broadcast <label> | <message>` – Send to group\n\n"
        "⏰ *SCHEDULER*\n"
        "  `/schedule <chat_id> | <time> | <msg>`\n"
        "  `/schedules` – View scheduled messages\n\n"
        "🗂 *ORGANIZER*\n"
        "  `/tag <chat_id> | <tag>` – Tag a chat\n"
        "  `/chats` – View tagged chats\n"
        "  `/note <title> | <content>` – Save a note\n"
        "  `/notes` – View all notes\n\n"
        "🎧 *AGENTS*\n"
        "  `/addagent <name> | <id> | <specialty>`\n"
        "  `/agents` – List support agents\n"
        "  `/agenton <id>` / `/agentoff <id>` – Availability\n\n"
        "👑 *TEAM*\n"
        "  `/addteam <user_id>` – Add team member\n"
        "  `/team` – List team\n"
        "  `/stats` – Bot statistics\n"
        "━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


@owner_only
async def add_team_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/addteam <user_id> <name>`", parse_mode="Markdown")
        return
    try:
        uid = int(context.args[0])
        name = " ".join(context.args[1:]) if len(context.args) > 1 else "Team Member"
        conn = get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO team (user_id, name, added_by) VALUES (?,?,?)",
            (uid, name, update.effective_user.id)
        )
        conn.commit()
        conn.close()
        TEAM_IDS.append(uid)
        await update.message.reply_text(f"✅ *{name}* (ID: `{uid}`) added to team!", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Must be a number.")


@owner_only
async def remove_team_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/removeteam <user_id>`", parse_mode="Markdown")
        return
    uid = int(context.args[0])
    conn = get_conn()
    conn.execute("DELETE FROM team WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()
    if uid in TEAM_IDS:
        TEAM_IDS.remove(uid)
    await update.message.reply_text(f"✅ User `{uid}` removed from team.", parse_mode="Markdown")


async def list_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    conn = get_conn()
    members = conn.execute("SELECT * FROM team").fetchall()
    conn.close()
    if not members:
        await update.message.reply_text("No team members yet.")
        return
    text = "👥 *Team Members:*\n━━━━━━━━━━━━━\n"
    for m in members:
        text += f"• *{m['name']}* — ID: `{m['user_id']}`\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_team_member(update):
        return
    conn = get_conn()
    total_pay     = conn.execute("SELECT COUNT(*) as c FROM payments").fetchone()['c']
    pending_pay   = conn.execute("SELECT COUNT(*) as c FROM payments WHERE status='pending'").fetchone()['c']
    confirmed_pay = conn.execute("SELECT COUNT(*) as c FROM payments WHERE status='confirmed'").fetchone()['c']
    total_replies = conn.execute("SELECT COUNT(*) as c FROM auto_replies").fetchone()['c']
    total_contacts= conn.execute("SELECT COUNT(*) as c FROM contacts").fetchone()['c']
    total_sched   = conn.execute("SELECT COUNT(*) as c FROM schedules WHERE status='pending'").fetchone()['c']
    total_notes   = conn.execute("SELECT COUNT(*) as c FROM notes").fetchone()['c']
    total_agents  = conn.execute("SELECT COUNT(*) as c FROM agents").fetchone()['c']
    online_agents = conn.execute("SELECT COUNT(*) as c FROM agents WHERE available=1").fetchone()['c']
    conn.close()

    await update.message.reply_text(
        "📊 *Bot Statistics*\n━━━━━━━━━━━━━\n"
        f"💰 Payments: `{total_pay}` total | `{pending_pay}` pending | `{confirmed_pay}` confirmed\n"
        f"🤖 Auto-replies: `{total_replies}`\n"
        f"👥 Contacts: `{total_contacts}`\n"
        f"🎧 Agents: `{total_agents}` total | `{online_agents}` online\n"
        f"⏰ Pending Schedules: `{total_sched}`\n"
        f"📝 Notes: `{total_notes}`",
        parse_mode="Markdown"
    )
